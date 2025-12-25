import xml.etree.ElementTree as ET

from jgo.maven.model import Model, ProfileConstraints


class MockPOM:
    groupId = "g"
    artifactId = "a"
    version = "v"
    name = "n"
    description = "d"
    properties = {}

    def elements(self, xpath):
        return []

    def element(self, xpath):
        return None


def test_profile_activation_os_match():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    os_elem = ET.SubElement(activation, "os")
    ET.SubElement(os_elem, "name").text = "Windows XP"

    constraints = ProfileConstraints(os_name="Windows XP")
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is True


def test_profile_activation_os_mismatch():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    os_elem = ET.SubElement(activation, "os")
    ET.SubElement(os_elem, "name").text = "Windows XP"

    constraints = ProfileConstraints(os_name="Linux")
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is False


def test_profile_activation_os_negation_match():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    os_elem = ET.SubElement(activation, "os")
    ET.SubElement(os_elem, "name").text = "!Windows XP"

    constraints = ProfileConstraints(os_name="Linux")
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is True


def test_profile_activation_os_negation_mismatch():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    os_elem = ET.SubElement(activation, "os")
    ET.SubElement(os_elem, "name").text = "!Windows XP"

    constraints = ProfileConstraints(os_name="Windows XP")
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is False


def test_profile_activation_os_missing_info_mismatch():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    os_elem = ET.SubElement(activation, "os")
    ET.SubElement(os_elem, "family").text = "Windows"

    # We provide name but not family. Should mismatch.
    constraints = ProfileConstraints(os_name="Linux")
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is False


def test_profile_activation_os_missing_info_negation_match():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    os_elem = ET.SubElement(activation, "os")
    ET.SubElement(os_elem, "family").text = "!Windows"

    # We provide name but not family. Should match !Windows because None != Windows.
    constraints = ProfileConstraints(os_name="Linux")
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is True


def test_profile_activation_property_match():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    prop = ET.SubElement(activation, "property")
    ET.SubElement(prop, "name").text = "foo"
    ET.SubElement(prop, "value").text = "bar"

    constraints = ProfileConstraints(properties={"foo": "bar"})
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is True


def test_profile_activation_property_mismatch():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    prop = ET.SubElement(activation, "property")
    ET.SubElement(prop, "name").text = "foo"
    ET.SubElement(prop, "value").text = "bar"

    constraints = ProfileConstraints(properties={"foo": "baz"})
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is False


def test_profile_activation_property_exists():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    prop = ET.SubElement(activation, "property")
    ET.SubElement(prop, "name").text = "foo"
    # No value means check for existence

    constraints = ProfileConstraints(properties={"foo": "anything"})
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is True


def test_profile_activation_property_missing():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    prop = ET.SubElement(activation, "property")
    ET.SubElement(prop, "name").text = "foo"

    constraints = ProfileConstraints(properties={"bar": "baz"})
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is False
