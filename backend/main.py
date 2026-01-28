from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from db import create_tables, create_default_admin_account

import routers.assignments
import routers.submissions
import routers.grades
import routers.courses
import routers.sections
import routers.materials
import routers.parents
import routers.students
import routers.teachers
import routers.users
import routers.personalization
import routers.admins


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create database tables on application startup."""
    create_tables()
    create_default_admin_account()
    yield


app = FastAPI(
    root_path="/api",
    title="EdHub",
    description="**Open API for platform management**\n\n"
    "EdHub is a Learning Management System for interaction between "
    "teachers, students, and parents. It aims to improve the quality "
    "of an educational process, simplify the interaction between "
    "stakeholders, and improve student engagement in learning.\n\n"
    "Any user can create a course becoming a Teacher, invite students "
    "and their parents, upload materials, create assignments, see "
    " student submissions, grade them based on criteria, and calculate "
    "course grade. You can also join the course as a Student to see the "
    "study materials and submit your homework or as a Parent to track "
    "the academic performance of your child.\n\n"
    "Most existing LMSs either have limited functionality or have awkward "
    "website design and cause difficulties in everyday use. EdHub combines "
    "a self-contained and clear design, supporting all the necessary "
    "features but not bogging the user down with complex customizations.",
    version="1.0",
    lifespan=lifespan,
)
app.include_router(routers.assignments.router)
app.include_router(routers.submissions.router)
app.include_router(routers.grades.router)
app.include_router(routers.courses.router)
app.include_router(routers.personalization.router)
app.include_router(routers.sections.router)
app.include_router(routers.materials.router)
app.include_router(routers.parents.router)
app.include_router(routers.students.router)
app.include_router(routers.teachers.router)
app.include_router(routers.users.router)
app.include_router(routers.admins.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
