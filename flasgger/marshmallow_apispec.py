# coding: utf-8
import inspect
from flask.views import MethodView
import flasgger

try:
    from marshmallow import Schema, fields
    from apispec.ext.marshmallow.swagger import (
        schema2jsonschema, schema2parameters
    )
except ImportError:
    Schema = None
    fields = None
    schema2jsonschema = lambda schema: {}  # noqa
    schema2parameters = lambda schema: []  # noqa


class SwaggerView(MethodView):
    """
    A Swagger view
    """
    parameters = []
    responses = {}
    definitions = {}
    tags = []
    consumes = ['application/json']
    produces = ['application/json']
    schemes = []
    security = []
    deprecated = False
    operationId = None
    externalDocs = {}
    summary = None
    description = None
    validation = False

    def dispatch_request(self, *args, **kwargs):
        if self.validation:
            specs = {}
            attrs = flasgger.constants.OPTIONAL_FIELDS + [
                'parameters', 'definitions', 'responses',
                'summary', 'description'
            ]
            for attr in attrs:
                specs[attr] = getattr(self, attr)
            definitions = {}
            specs.update(convert_schemas(specs, definitions))
            specs['definitions'] = definitions
            flasgger.utils.validate(specs=specs)
        return super(SwaggerView, self).dispatch_request(*args, **kwargs)


def convert_schemas(d, definitions=None):
    if Schema is None:
        raise RuntimeError('Please install marshmallow and apispec')

    new = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = convert_schemas(v, definitions)
        if isinstance(v, (list, tuple)):
            new_v = []
            for item in v:
                if isinstance(item, dict):
                    new_v.append(convert_schemas(item, definitions))
                else:
                    new_v.append(item)
            v = new_v
        if inspect.isclass(v) and issubclass(v, Schema):
            definitions[v.__name__] = schema2jsonschema(v)
            ref = {
               "$ref": "#/definitions/{0}".format(v.__name__)
            }
            if k == 'parameters':
                new[k] = schema2parameters(v)
                new[k][0]['schema'] = ref
            else:
                new[k] = ref
        else:
            new[k] = v

        if k == 'definitions':
            new['definitions'] = definitions
    return new