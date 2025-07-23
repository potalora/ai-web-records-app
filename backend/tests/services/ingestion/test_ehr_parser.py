import json
import pytest
from pathlib import Path
from fhir.resources.bundle import Bundle
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation

from src.services.ingestion.ehr_parser import parse_fhir_resource, FHIRParsingError

# Define the fixtures directory relative to the test file
FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'

@pytest.fixture
def sample_fhir_bundle_path(tmp_path: Path) -> Path:
    """Creates a sample valid FHIR Bundle JSON file in a temporary directory."""
    bundle_data = {
        "resourceType": "Bundle",
        "id": "bundle-example-1",
        "type": "collection",
        "entry": [
            {
                "fullUrl": "http://example.org/fhir/Patient/pat1",
                "resource": {
                    "resourceType": "Patient",
                    "id": "pat1",
                    "name": [{
                        "use": "official",
                        "family": "Doe",
                        "given": ["John"]
                    }]
                }
            }
        ]
    }
    file_path = tmp_path / "sample_bundle.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(bundle_data, f)
    return file_path

@pytest.fixture
def invalid_json_path(tmp_path: Path) -> Path:
    """Creates an invalid JSON file."""
    file_path = tmp_path / "invalid.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("{\"key\": \"value\"") # Missing closing brace
    return file_path

@pytest.fixture
def not_fhir_json_path(tmp_path: Path) -> Path:
    """Creates a valid JSON file that is not a FHIR resource."""
    file_path = tmp_path / "not_fhir.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({"hello": "world"}, f) # Missing resourceType
    return file_path

@pytest.fixture
def sample_fhir_patient_xml_path(tmp_path: Path) -> Path:
    """Creates a sample valid FHIR Patient XML file in a temporary directory."""
    patient_data = """
    <Patient xmlns="http://hl7.org/fhir">
        <id value="patient-example-1"/>
        <gender value="male"/>
    </Patient>
    """
    file_path = tmp_path / "sample_patient.xml"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(patient_data)
    return file_path

@pytest.fixture
def sample_fhir_bundle_xml_path(tmp_path: Path) -> Path:
    """Creates a sample valid FHIR Bundle XML file in a temporary directory."""
    bundle_data = """
    <Bundle xmlns="http://hl7.org/fhir">
        <id value="bundle-example-xml"/>
        <entry>
            <resource>
                <Patient>
                    <id value="pat1"/>
                    <name>
                        <family value="Doe"/>
                        <given value="John"/>
                    </name>
                </Patient>
            </resource>
        </entry>
        <entry>
            <resource>
                <Observation>
                    <id value="obs1"/>
                    <status value="final"/>
                </Observation>
            </resource>
        </entry>
    </Bundle>
    """
    file_path = tmp_path / "sample_bundle.xml"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(bundle_data)
    return file_path

@pytest.fixture
def invalid_syntax_xml_path(tmp_path: Path) -> Path:
    """Creates an invalid XML file."""
    file_path = tmp_path / "invalid_syntax.xml"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("<Patient xmlns='http://hl7.org/fhir'><id value='patient-example-1'/>") # Missing closing tag
    return file_path

@pytest.fixture
def not_fhir_xml_path(tmp_path: Path) -> Path:
    """Creates a valid XML file that is not a FHIR resource."""
    file_path = tmp_path / "not_fhir.xml"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("<myData><hello>world</hello></myData>") # Not a FHIR resource
    return file_path

def test_parse_valid_fhir_bundle(sample_fhir_bundle_path: Path):
    """Tests parsing a valid FHIR Bundle JSON file."""
    resource = parse_fhir_resource(sample_fhir_bundle_path)
    assert isinstance(resource, Bundle)
    assert resource.id == "bundle-example-1"
    assert len(resource.entry) == 1
    assert isinstance(resource.entry[0].resource, Patient)
    assert resource.entry[0].resource.id == "pat1"

def test_parse_file_not_found():
    """Tests parsing a non-existent file."""
    with pytest.raises(FileNotFoundError):
        parse_fhir_resource("non_existent_file.json")

def test_parse_invalid_json(tmp_path):
    """Test parsing an invalid JSON file raises FHIRParsingError."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text('{"key": "value",}') # Invalid JSON (trailing comma) - Corrected quotes
    
    # Expect FHIRParsingError, check message contains lxml specific error
    with pytest.raises(FHIRParsingError, match=r"File .* is not valid JSON or XML: XML syntax error:"):
        parse_fhir_resource(invalid_file)

def test_parse_not_fhir_json(not_fhir_json_path: Path):
    """Tests parsing valid JSON that isn't a FHIR resource (missing resourceType)."""
    # fhir.resources.construct might raise various specific errors, FHIRParsingError wraps them.
    with pytest.raises(FHIRParsingError):
        parse_fhir_resource(not_fhir_json_path)

def test_parse_valid_fhir_patient_xml(sample_fhir_patient_xml_path: Path):
    """Tests parsing a valid FHIR Patient XML file."""
    resource = parse_fhir_resource(sample_fhir_patient_xml_path)
    assert isinstance(resource, Patient)
    assert resource.id == "patient-example-1"
    assert resource.gender == "male"

def test_parse_valid_fhir_bundle_xml(sample_fhir_bundle_xml_path: Path):
    """Tests parsing a valid FHIR Bundle XML file."""
    resource = parse_fhir_resource(sample_fhir_bundle_xml_path)
    assert isinstance(resource, Bundle)
    assert resource.id == "bundle-example-xml"
    assert len(resource.entry) == 2
    # Check resource types within the bundle
    resource_types_in_bundle = [entry.resource.resource_type for entry in resource.entry]
    assert "Patient" in resource_types_in_bundle
    assert "Observation" in resource_types_in_bundle

def test_parse_invalid_syntax_xml(invalid_syntax_xml_path: Path):
    """Tests parsing an XML file with invalid syntax."""
    # Expect FHIRParsingError which wraps the underlying XMLSyntaxError
    with pytest.raises(FHIRParsingError):
        parse_fhir_resource(invalid_syntax_xml_path)

def test_parse_not_fhir_xml(not_fhir_xml_path: Path):
    """Tests parsing a valid XML file that is not a FHIR resource."""
    # Expect FHIRParsingError because _get_model_class will fail to find 'myData'
    with pytest.raises(FHIRParsingError):
        parse_fhir_resource(not_fhir_xml_path)

def test_parse_invalid_xml(tmp_path):
    """Test parsing an invalid XML file raises FHIRParsingError."""
    # ... (rest of the code remains the same)
