"""
wdai v3.0 - Workflow Templates
SOP工作流引擎 - 模板库
"""

from .common import (
    SoftwareDevTemplate,
    DataProcessingTemplate,
    TestAutomationTemplate,
    DeployTemplate,
    get_template,
    list_templates
)

__all__ = [
    "SoftwareDevTemplate",
    "DataProcessingTemplate",
    "TestAutomationTemplate",
    "DeployTemplate",
    "get_template",
    "list_templates"
]
