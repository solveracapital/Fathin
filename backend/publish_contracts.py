import json
from pathlib import Path
from .app import app
from .schemas import AnalysisResult,Metric,Visual

root=Path(__file__).resolve().parents[1]/'contracts'
root.mkdir(exist_ok=True)
(root/'schemas').mkdir(exist_ok=True)
(root/'openapi.json').write_text(json.dumps(app.openapi(),indent=2),encoding='utf-8')
for model in (AnalysisResult,Metric,Visual):
    (root/'schemas'/f'{model.__name__}.json').write_text(json.dumps(model.model_json_schema(),indent=2),encoding='utf-8')
print('OpenAPI and schemas published')
