import pytest

from datahub.ingestion.run.pipeline import Pipeline
from tests.test_helpers import mce_helpers
from tests.test_helpers.docker_helpers import wait_for_port


@pytest.mark.slow
def test_mongodb_ingest(docker_compose_runner, pytestconfig, tmp_path, mock_time):
    test_resources_dir = pytestconfig.rootpath / "tests/integration/mongodb"

    with docker_compose_runner(
        test_resources_dir / "docker-compose.yml", "mongo"
    ) as docker_services:
        wait_for_port(docker_services, "testmongodb", 27017)

        # Run the metadata ingestion pipeline.
        pipeline = Pipeline.create(
            {
                "run_id": "mongodb-test",
                "source": {
                    "type": "mongodb",
                    "config": {
                        "connect_uri": "mongodb://localhost:57017",
                        "username": "mongoadmin",
                        "password": "examplepass",
                    },
                },
                "sink": {
                    "type": "file",
                    "config": {
                        "filename": f"{tmp_path}/mongodb_mces.json",
                    },
                },
            }
        )
        pipeline.run()
        pipeline.raise_from_status()

        # Verify the output.
        output = mce_helpers.load_json_file(str(tmp_path / "mongodb_mces.json"))
        golden = mce_helpers.load_json_file(
            str(test_resources_dir / "mongodb_mce_golden.json")
        )
        mce_helpers.assert_mces_equal(output, golden)
