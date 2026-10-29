"""Unit tests for the pan-tilt domain, with in-memory fakes at the hardware/MQTT boundaries."""

from __future__ import annotations

import json

import pytest

from domain import (
    AXES,
    BASE,
    DEFAULT,
    HD,
    LIGHT,
    RETIRED,
    STEP_US,
    Agent,
    clamp,
    discovery_configs,
    pulse_for,
    ramp,
)


class FakeServos:
    def __init__(self):
        self.calls = []

    def write_pulse(self, channel, us):
        self.calls.append(("pulse", channel, us))

    def cut(self, channel):
        self.calls.append(("cut", channel))


class FakeCamera:
    def __init__(self, image=b"jpeg"):
        self.image, self.shots = image, []

    def capture(self, width, height, quality):
        self.shots.append((width, height, quality))
        return self.image


class FakeBus:
    def __init__(self):
        self.messages = []

    def publish(self, topic, payload, retain=False):
        self.messages.append((topic, payload, retain))

    def last(self, topic):
        return [p for t, p, _ in self.messages if t == topic][-1]


class FakeStore:
    def __init__(self, **data):
        self.data = data

    def load(self, name):
        return self.data.get(name)

    def save(self, name, data):
        self.data[name] = json.loads(json.dumps(data))


def make_agent(camera=None, store=None):
    servos, bus = FakeServos(), FakeBus()
    agent = Agent(
        servos,
        camera or FakeCamera(),
        bus,
        store or FakeStore(),
        sleep=lambda _s: None,
        run_later=lambda task: task(),
    )
    return agent, servos, bus


@pytest.fixture
def agent():
    return make_agent()[0]


def drain(agent):
    while not agent.moves.empty():
        agent.next_move()


# --- servo safety -------------------------------------------------------------------
@pytest.mark.parametrize("axis", ["pan", "tilt"])
@pytest.mark.parametrize(
    "position,key", [(0, "centre"), (100, "plus"), (-100, "minus")]
)
def test_pulse_hits_the_calibrated_points(axis, position, key):
    assert pulse_for(axis, position) == AXES[axis][key]


@pytest.mark.parametrize("axis", ["pan", "tilt"])
@pytest.mark.parametrize("position", [-1000, -101, 101, 1e6])
def test_pulse_never_leaves_the_calibrated_limits(axis, position):
    low, high = sorted((AXES[axis]["minus"], AXES[axis]["plus"]))
    assert low <= pulse_for(axis, position) <= high


def test_pan_halfway_is_linear():
    assert pulse_for("pan", 50) == round(1625 + (2750 - 1625) / 2)


@pytest.mark.parametrize(
    "value,expected", [(150, 100), (-150, -100), (42.4, 42), (0, 0)]
)
def test_clamp(value, expected):
    assert clamp(value) == expected


def test_ramp_steps_up_and_ends_on_goal():
    assert ramp(1000, 1050) == [1000, 1020, 1040, 1050]


def test_ramp_steps_down_never_faster_than_one_step():
    assert ramp(1050, 1000) == [1050, 1030, 1010, 1000]
    steps = ramp(2300, 500)
    assert all(abs(b - a) <= STEP_US for a, b in zip(steps, steps[1:]))


def test_ramp_to_same_position_only_holds_it():
    assert ramp(1500, 1500) == [1500]


def test_move_ramps_then_cuts_the_signal():
    agent, servos, _ = make_agent()
    agent.move("pan", 10)
    channel = AXES["pan"]["channel"]
    assert servos.calls[-1] == ("cut", channel)
    pulses = [call[2] for call in servos.calls[:-1]]
    assert pulses[0] == AXES["pan"]["centre"]
    assert pulses[-1] == pulse_for("pan", 10)
    assert agent.state["pan"] == 10


def test_move_from_an_offset_ramps_from_the_last_position():
    agent, servos, _ = make_agent()
    agent.state["pan"] = 50
    agent.move("pan", -50)
    pulses = [call[2] for call in servos.calls if call[0] == "pulse"]
    assert pulses[0] == pulse_for("pan", 50)
    assert pulses[-1] == pulse_for("pan", -50)
    assert all(abs(b - a) <= STEP_US for a, b in zip(pulses, pulses[1:]))


def test_failed_move_still_cuts_the_signal_and_keeps_the_state():
    agent, servos, _ = make_agent()

    def broken_write(channel, us):
        servos.calls.append(("pulse", channel, us))
        if len(servos.calls) == 3:
            raise OSError("I2C error")

    servos.write_pulse = broken_write
    with pytest.raises(OSError):
        agent.move("pan", 50)
    assert servos.calls[-1] == ("cut", AXES["pan"]["channel"])
    assert agent.state["pan"] == 0


@pytest.mark.parametrize("axis", ["pan", "tilt"])
@pytest.mark.parametrize("target,end", [(500, "plus"), (-500, "minus")])
def test_move_beyond_limits_is_clamped(axis, target, end):
    agent, servos, _ = make_agent()
    agent.move(axis, target)
    low, high = sorted((AXES[axis]["minus"], AXES[axis]["plus"]))
    pulses = [call[2] for call in servos.calls if call[0] == "pulse"]
    assert all(low <= us <= high for us in pulses)
    assert pulses[-1] == AXES[axis][end]
    assert agent.state[axis] == (100 if target > 0 else -100)


# --- commands -----------------------------------------------------------------------
def test_pan_command_is_queued_then_moved_saved_reported():
    store = FakeStore()
    agent, _, bus = make_agent(store=store)
    agent.handle(f"{BASE}/pan/set", " 35 ")
    drain(agent)
    assert agent.state["pan"] == 35
    assert store.data["state"]["pan"] == 35
    assert bus.last(f"{BASE}/pan/state") == "35"
    assert agent.shoot_now.is_set()


@pytest.mark.parametrize("payload", ["abc", "", "1,5", "inf", "-inf", "nan", "1e999"])
def test_malformed_move_is_ignored(agent, payload):
    agent.handle(f"{BASE}/tilt/set", payload)
    assert agent.moves.empty()


def test_unknown_topic_is_ignored():
    agent, _, bus = make_agent()
    agent.handle(f"{BASE}/reboot", "now")
    assert agent.moves.empty()
    assert bus.messages == []


def test_privacy_off_blanks_images_and_skips_capture():
    camera = FakeCamera()
    agent, _, bus = make_agent(camera=camera)
    agent.handle(f"{BASE}/privacy/set", "OFF")
    agent.want_hd.set()
    agent.shoot()
    assert camera.shots == []
    assert bus.last(f"{BASE}/camera") == b""
    assert bus.last(f"{BASE}/camera_hd") == b""
    assert bus.last(f"{BASE}/privacy/state") == "OFF"
    assert not agent.want_hd.is_set()


def test_privacy_off_during_capture_drops_the_image():
    agent, _, bus = make_agent()

    class SlowCamera:
        def capture(self, width, height, quality):
            agent.handle(f"{BASE}/privacy/set", "OFF")  # arrives mid-capture
            return b"jpeg"

    agent.camera = SlowCamera()
    agent.shoot()
    assert all(payload != b"jpeg" for _, payload, _ in bus.messages)


def test_privacy_rejects_other_values(agent):
    agent.handle(f"{BASE}/privacy/set", "OFF")
    agent.handle(f"{BASE}/privacy/set", "maybe")
    assert agent.state["camera"] == "OFF"


def test_hd_request_publishes_hd_then_light():
    camera = FakeCamera()
    agent, _, bus = make_agent(camera=camera)
    agent.handle(f"{BASE}/snapshot_hd", "PRESS")
    agent.shoot()
    assert camera.shots == [HD, LIGHT]
    assert bus.last(f"{BASE}/camera_hd") == b"jpeg"
    assert not agent.want_hd.is_set()


def test_failed_capture_publishes_nothing():
    agent, _, bus = make_agent(camera=FakeCamera(b""))
    agent.shoot()
    assert all(topic != f"{BASE}/camera" for topic, _, _ in bus.messages)


# --- saved positions ----------------------------------------------------------------
def test_save_preset_under_typed_name():
    store = FakeStore()
    agent, _, bus = make_agent(store=store)
    agent.state.update(pan=20, tilt=-10)
    agent.handle(f"{BASE}/preset_name/set", "Porte")
    assert store.data["presets"]["Porte"] == [20, -10]
    assert bus.last(f"{BASE}/preset/state") == "Porte"
    assert bus.last(f"{BASE}/preset_name/state") == ""
    config = json.loads(bus.last("homeassistant/select/pi3_preset/config"))
    assert config["options"] == [DEFAULT, "Porte", "🗑 Supprimer « Porte »"]


def test_preset_name_is_truncated(agent):
    agent.handle(f"{BASE}/preset_name/set", "x" * 50)
    assert list(agent.presets) == [DEFAULT, "x" * 30]


@pytest.mark.parametrize("name", ["", "🗑 Supprimer « Porte »", "🗑 trash"])
def test_trash_prefix_and_empty_names_are_reserved(agent, name):
    agent.handle(f"{BASE}/preset_name/set", name)
    assert list(agent.presets) == [DEFAULT]


def test_go_to_preset_moves_both_axes_and_republishes():
    agent, _, bus = make_agent()
    agent.presets["Porte"] = [30, 40]
    agent.handle(f"{BASE}/preset/set", "Porte")
    assert list(agent.moves.queue) == [("pan", 30), ("tilt", 40)]
    assert bus.last(f"{BASE}/preset/state") == "Porte"
    drain(agent)
    assert (agent.state["pan"], agent.state["tilt"]) == (30, 40)
    assert agent.selected == "Porte"


def test_default_preset_recentres(agent):
    agent.state.update(pan=60, tilt=60)
    agent.handle(f"{BASE}/preset/set", DEFAULT)
    drain(agent)
    assert (agent.state["pan"], agent.state["tilt"]) == (0, 0)


def test_delete_option_removes_the_selected_preset():
    store = FakeStore()
    agent, _, bus = make_agent(store=store)
    agent.handle(f"{BASE}/preset_name/set", "Porte")
    agent.handle(f"{BASE}/preset/set", "🗑 Supprimer « Porte »")
    config = json.loads(bus.last("homeassistant/select/pi3_preset/config"))
    assert config["options"] == [DEFAULT]
    assert "Porte" not in agent.presets
    assert agent.selected == DEFAULT
    assert "Porte" not in store.data["presets"]


def test_default_position_cannot_be_deleted(agent):
    agent.handle(f"{BASE}/preset/set", f"🗑 Supprimer « {DEFAULT} »")
    assert DEFAULT in agent.presets


def test_default_offers_no_delete_option(agent):
    assert agent.preset_options() == [DEFAULT]


def test_state_and_presets_survive_a_restart():
    store = FakeStore(
        state={"pan": 15, "tilt": 5, "camera": "OFF"}, presets={"Porte": [1, 2]}
    )
    agent, _, _ = make_agent(store=store)
    assert agent.state == {"pan": 15, "tilt": 5, "camera": "OFF"}
    assert agent.presets == {DEFAULT: [0, 0], "Porte": [1, 2]}


@pytest.mark.parametrize(
    "state,presets",
    [
        ({"pan": "x", "tilt": float("inf"), "camera": "MAYBE"}, {"a": [1], "b": "no"}),
        ({"pan": True, "tilt": None}, {"c": [1, float("nan")], "d": [1, "2"]}),
    ],
)
def test_bad_stored_data_falls_back_to_defaults(state, presets):
    agent, _, _ = make_agent(store=FakeStore(state=state, presets=presets))
    assert agent.state == {"pan": 0, "tilt": 0, "camera": "ON"}
    assert agent.presets == {DEFAULT: [0, 0]}


def test_stored_positions_are_clamped():
    store = FakeStore(state={"pan": 400}, presets={"Loin": [-300, 300]})
    agent, _, _ = make_agent(store=store)
    assert agent.state["pan"] == 100
    assert agent.presets["Loin"] == [-100, 100]


def test_wait_for_shot_consumes_the_request(agent):
    agent.shoot_now.set()
    agent.wait_for_shot(0)
    assert not agent.shoot_now.is_set()


# --- discovery ----------------------------------------------------------------------
def test_on_connect_announces_availability_entities_and_state():
    agent, _, bus = make_agent()
    agent.on_connect()
    assert bus.messages[0] == (f"{BASE}/status", "online", True)
    assert all(retain for topic, _, retain in bus.messages if "/camera" not in topic)
    topics = {topic for topic, _, _ in bus.messages}
    assert set(discovery_configs()) <= topics
    assert {f"{BASE}/pan/state", f"{BASE}/preset/state"} <= topics


def test_discovery_retires_dropped_entities_and_shares_the_device():
    configs = discovery_configs()
    for path in RETIRED:
        assert configs[f"homeassistant/{path}/config"] == ""
    live = [json.loads(payload) for payload in configs.values() if payload]
    assert all(c["availability_topic"] == f"{BASE}/status" for c in live)
    assert len({c["unique_id"] for c in live}) == len(live)
