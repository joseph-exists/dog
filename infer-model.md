_cli.py:from .models import KnownModelName, infer_model
_cli.py:            agent.model = infer_model(args.model or default_model)
agent/__init__.py:            self._model = models.infer_model(model)
agent/__init__.py:                _utils.Some(models.infer_model(model))
agent/__init__.py:            model_ = models.infer_model(model)
agent/__init__.py:            model_ = self.model = models.infer_model(self.model)
agent/__init__.py:                models.infer_model(model) if model else self._get_model(None)
models/__init__.py:def infer_model(  # noqa: C901
models/wrapper.py:from . import KnownModelName, Model, ModelRequestParameters, StreamedResponse, infer_model
models/wrapper.py:        self.wrapped = infer_model(wrapped)
models/fallback.py:from . import KnownModelName, Model, ModelRequestParameters, StreamedResponse, infer_model
models/fallback.py:        self.models = [infer_model(default_model), *[infer_model(m) for m in fallback_models]]
direct.py:    model_instance = models.infer_model(model)
