from fastapi import APIRouter

from .routes.survey import router as survey_router
from .routes.faculty_scores import router as faculty_scores_router
from .routes.sankey import router as sankey_router

from .routes.knowledge import router as knowledge_router
from .routes.uses import router as uses_router
from .routes.tools import router as tools_router
from .routes.perceptions import router as perceptions_router
from .routes.training import router as training_router
from .routes.open_text import router as open_text_router

router = APIRouter(prefix="/api", tags=["Visualizations"])

router.include_router(survey_router)
router.include_router(faculty_scores_router)
router.include_router(sankey_router)

router.include_router(knowledge_router)
router.include_router(uses_router)
router.include_router(tools_router)
router.include_router(perceptions_router)
router.include_router(training_router)
router.include_router(open_text_router)
