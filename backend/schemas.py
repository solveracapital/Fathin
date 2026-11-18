"""Published result contract for generated frontend types."""
from typing import Literal,Any
from pydantic import BaseModel,Field,model_validator

class Reason(BaseModel):
    code:str
    message:str
class Metric(BaseModel):
    id:str
    label:str
    value:float|None
    unit:Literal['count','ratio','percent','score','none']
    subset_id:str
    status:Literal['ok','undefined','unavailable']
    reason:Reason|None
    evidence_ids:list[str]
    @model_validator(mode='after')
    def consistent(self):
        if self.status=='ok' and self.value is None:raise ValueError('ok requires a value')
        if self.status!='ok' and (self.value is not None or self.reason is None):raise ValueError('Undefined metric must have null value and reason')
        return self
class Visual(BaseModel):
    id:str
    kind:Literal['bar','histogram','boxplot','heatmap','line','scatter','biplot','scree','dendrogram','confusion_matrix','roc','precision_recall','silhouette','contribution']
    title:str
    purpose:str
    status:Literal['shown','available','omitted','unavailable']
    reason_code:str
    reason_text:str
    data_ref:str|None
    subset_id:str
    axes:dict
    series:list
    encodings:dict
    evidence_ids:list[str]
    projection:dict|None
    sampling:dict|None
    default_order:int
    table_alternative_ref:str|None
    @model_validator(mode='after')
    def shown_has_data(self):
        if self.status=='shown' and (not self.data_ref or not self.table_alternative_ref):raise ValueError('Shown visual requires data and table')
        return self
class AnalysisResult(BaseModel):
    schema_version:Literal['1.0.0']
    run_id:str
    method:Literal['lda','pca','efa','kmeans','hierarchical']
    subset_definitions:dict
    metrics:list[Metric]
    table_index:list[dict]
    formula_index:list[dict]
    diagnostics:list[dict]
    narrative_blocks:list[dict]
    visual_manifest:list[Visual]
    provenance:dict
