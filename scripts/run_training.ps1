python -m src.data_pipeline prepare --params params.yaml
python -m src.train --params params.yaml
python -m src.evaluate --params params.yaml

