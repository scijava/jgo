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


# JDK activation tests


def test_profile_activation_jdk_exact_match():
    profile = ET.Element("profile")
    ET.SubElement(profile, "id").text = "java8"
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "1.8"

    constraints = ProfileConstraints(jdk="1.8.0_292")
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is True


def test_profile_activation_jdk_exact_mismatch():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "11"

    constraints = ProfileConstraints(jdk="1.8")
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is False


def test_profile_activation_jdk_range_inclusive():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "[1.8,11]"

    # Test lower bound
    constraints = ProfileConstraints(jdk="1.8")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    # Test middle
    constraints = ProfileConstraints(jdk="9")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    # Test upper bound
    constraints = ProfileConstraints(jdk="11")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    # Test outside range
    constraints = ProfileConstraints(jdk="17")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is False


def test_profile_activation_jdk_range_exclusive():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "(1.8,11)"

    constraints = ProfileConstraints(jdk="9")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    # Boundary excluded
    constraints = ProfileConstraints(jdk="1.8")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is False


def test_profile_activation_jdk_minimum_version():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "[11,)"

    constraints = ProfileConstraints(jdk="11")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    constraints = ProfileConstraints(jdk="17")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    constraints = ProfileConstraints(jdk="8")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is False


def test_profile_activation_jdk_negation():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "!1.8"

    constraints = ProfileConstraints(jdk="11")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    constraints = ProfileConstraints(jdk="1.8")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is False


def test_profile_activation_jdk_negation_range():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "![1.8,11)"

    constraints = ProfileConstraints(jdk="11")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    constraints = ProfileConstraints(jdk="9")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is False


def test_profile_activation_jdk_missing_constraints():
    """Profile should not activate if no java_version in constraints."""
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "11"

    constraints = ProfileConstraints()  # No java_version
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is False


def test_profile_activation_jdk_invalid_spec():
    """Invalid JDK spec should be logged and skipped, not crash."""
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "invalid[range"

    constraints = ProfileConstraints(jdk="11")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    # Should not activate and should not raise exception
    assert model._is_active_profile(profile) is False


def test_profile_activation_jdk_semantic_versioning():
    """Test that patch versions are compared correctly."""
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    ET.SubElement(activation, "jdk").text = "[1.8.0_191,1.8.0_292]"

    # Within range
    constraints = ProfileConstraints(jdk="1.8.0_250")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is True

    # Below range
    constraints = ProfileConstraints(jdk="1.8.0_100")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is False

    # Above range
    constraints = ProfileConstraints(jdk="1.8.0_300")
    model = Model(MockPOM(), None, profile_constraints=constraints)
    assert model._is_active_profile(profile) is False


# File activation tests


def test_profile_activation_file_exists():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    file_elem = ET.SubElement(activation, "file")
    ET.SubElement(file_elem, "exists").text = "/path/to/file.txt"

    # Mock file_exists to return True
    constraints = ProfileConstraints(
        file_exists=lambda path: path == "/path/to/file.txt"
    )
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is True


def test_profile_activation_file_exists_false():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    file_elem = ET.SubElement(activation, "file")
    ET.SubElement(file_elem, "exists").text = "/path/to/file.txt"

    # Mock file_exists to return False
    constraints = ProfileConstraints(file_exists=lambda path: False)
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is False


def test_profile_activation_file_missing():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    file_elem = ET.SubElement(activation, "file")
    ET.SubElement(file_elem, "missing").text = "/path/to/missing.txt"

    # Mock file_exists to return False (file is missing)
    constraints = ProfileConstraints(file_exists=lambda path: False)
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is True


def test_profile_activation_file_missing_false():
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    file_elem = ET.SubElement(activation, "file")
    ET.SubElement(file_elem, "missing").text = "/path/to/file.txt"

    # Mock file_exists to return True (file is NOT missing)
    constraints = ProfileConstraints(file_exists=lambda path: True)
    model = Model(MockPOM(), None, profile_constraints=constraints)

    assert model._is_active_profile(profile) is False


def test_profile_activation_file_interpolation():
    """Test that file paths are interpolated with properties."""
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    file_elem = ET.SubElement(activation, "file")
    ET.SubElement(file_elem, "exists").text = "${user.home}/.m2/settings.xml"

    # Create mock POM with properties
    pom = MockPOM()
    pom.properties = {"user.home": "/home/testuser"}

    # Track which path was checked
    checked_path = None

    def mock_exists(path):
        nonlocal checked_path
        checked_path = path
        return True

    constraints = ProfileConstraints(
        properties={"user.home": "/home/testuser"}, file_exists=mock_exists
    )
    model = Model(pom, None, profile_constraints=constraints)

    model._is_active_profile(profile)

    # Verify path was interpolated
    assert checked_path == "/home/testuser/.m2/settings.xml"


def test_profile_activation_file_basedir_interpolation():
    """Test that ${basedir} is interpolated when provided."""
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    file_elem = ET.SubElement(activation, "file")
    ET.SubElement(file_elem, "exists").text = "${basedir}/pom.xml"

    # Provide basedir in constraints
    checked_path = None

    def mock_exists(path):
        nonlocal checked_path
        checked_path = path
        return True

    constraints = ProfileConstraints(
        basedir="/home/user/project", file_exists=mock_exists
    )
    model = Model(MockPOM(), None, profile_constraints=constraints)

    model._is_active_profile(profile)

    # Should interpolate basedir
    assert checked_path == "/home/user/project/pom.xml"


def test_profile_activation_file_basedir_uninterpolated():
    """Test that ${basedir} remains uninterpolated when not provided."""
    profile = ET.Element("profile")
    activation = ET.SubElement(profile, "activation")
    file_elem = ET.SubElement(activation, "file")
    ET.SubElement(file_elem, "exists").text = "${basedir}/pom.xml"

    # No basedir in constraints
    checked_path = None

    def mock_exists(path):
        nonlocal checked_path
        checked_path = path
        return False

    constraints = ProfileConstraints(file_exists=mock_exists)
    model = Model(MockPOM(), None, profile_constraints=constraints)

    model._is_active_profile(profile)

    # Should check the literal un-interpolated path
    assert checked_path == "${basedir}/pom.xml"
