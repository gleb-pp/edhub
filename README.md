<div align="center">

`Python` • `FastAPI` • `Pydantic` • `SQLAlchemy` • `PostgreSQL`  
`Docker` • `GitHub Actions` • `Poetry` • `Pytest` • `Ruff` • `Mypy`

</div>

# 🎓 What is EdHub?

EdHub is a Learning Management System designed to facilitate interaction among teachers, students, and parents. It enhances the educational process by simplifying communication between stakeholders and increasing student engagement in learning.

When developing EdHub, we focused on the following priorities:

- **Quick Start for Teachers**: Teachers can easily create a course by simply entering its title, invite students and their parents, upload learning materials, and create assignments.

- **Student Assignment Submissions**: Students can access course materials, submit their solutions to assignments, and receive grades from the teacher. Teachers can review submitted work, evaluate solutions, and provide grades.

- **Parental Access to Track Academic Progress**: Parents have a special role in EdHub. Once invited to a course, they can track their child's academic progress without having to ask for a student account or contact the teacher.

# 🏗️ Implementation Details

The project provides a fully functional REST API with a clean backend architecture,
well-defined API design, and clear separation of business logic.

*Note:* This repository currently focuses on the **backend** part of the system. The frontend is not included and is expected to be developed separately.

### Project Goals

- Design a clean and maintainable architecture
- Separate business logic, access control, and transport layer concerns
- Build a backend suitable for real-world extension and scaling
- Create a portfolio-quality backend project for future development

### Architecture Layers

The backend is structured into several layers to ensure maintainability and scalability:

- `repo`: SQLAlchemy ORM models representing database entities and relationships.
- `services`: Stateless service classes encapsulating business logic through atomic operations.
- `policies`: Authorization and access-control rules, separated from business logic.
- `routers`: HTTP layer responsible for request validation, dependency injection, transaction boundaries, and exception-to-HTTP mapping.

### Built With

| Category | Technologies |
| :--- | :--- |
| **Framework & API** | <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" height="20"> <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python" height="20"> |
| **Database** | <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" height="20"> <img src="https://img.shields.io/badge/SQLAlchemy-3673A5?logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" height="20"> |
| **Infrastructure** | <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker" height="20"> <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white" alt="GitHub Actions" height="20"> |
| **Code Quality** | <img src="https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white" alt="Pytest" height="20"> <img src="https://img.shields.io/badge/Ruff-000000?logo=ruff&logoColor=white" alt="Ruff" height="20"> |

#### Core Technologies

[![Python][Python]][Python-url]
[![FastAPI][FastAPI]][FastAPI-url]
[![Pydantic][Pydantic]][Pydantic-url]
[![SQLAlchemy][SQLAlchemy]][SQLAlchemy-url]
[![Poetry][Poetry]][Poetry-url]

#### Testing & Code Quality

[![Pytest][Pytest]][Pytest-url]
[![Ruff][Ruff]][Ruff-url]
[![Mypy][Mypy]][Mypy-url]

#### Infrastructure

[![PostgreSQL][PostgreSQL]][PostgreSQL-url]
[![Docker][Docker]][Docker-url]
[![Docker Compose][Docker Compose]][Docker Compose-url]
[![GitHub Actions][GitHub Actions]][GitHub Actions-url]

# 🚀 Local Startup

EdHub is an open-source project, and you can run it locally to test its features, make your own improvements, and contribute to its development. By running EdHub on your local machine, you can ensure that all your organization's data remains private and secure.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)

### Quick Start
```bash
# Clone repository
git clone https://github.com/gleb-pp/edhub.git
cd edhub

# Build and start containers
docker compose up --build

# To run in detached mode:
# docker compose up --build -d

# To stop containers:
docker compose down
```

Now you can go to http://localhost/api/docs/ to access the application.

# 🤝 Contributing

EdHub is an open-source, non-commercial project developed primarily as a
portfolio and educational initiative and currently maintained by a single author.

### Support the Project
If you find this project interesting or useful:
- Giving the repository a ⭐ star is very important and highly appreciated
- Following the author on GitHub helps support further development

Even small actions like these provide strong motivation to continue improving the project.

### Frontend Development
At the moment, the project does not include a production-ready frontend.
The previous frontend implementation was removed, and a new one is not yet available.

The backend API is fully functional and can be used as a foundation
for experimenting with frontend development, educational projects,
or personal portfolio work.

Please note that:
- The project is not commercial
- Frontend contributions are not paid
- Any frontend work would be driven by personal interest and portfolio goals

### Bug Reports and Feedback
Bug reports, issue discussions, and general feedback are welcome.
If you notice unexpected behavior or have suggestions regarding usability
or documentation, feel free to open an issue.

[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[FastAPI]: https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi
[FastAPI-url]: https://fastapi.tiangolo.com/
[Pydantic]: https://img.shields.io/badge/Pydantic-176DC3?style=for-the-badge&logo=pydantic&logoColor=white
[Pydantic-url]: https://pydantic.dev/
[SQLAlchemy]: https://img.shields.io/badge/SQLAlchemy-3673A5?style=for-the-badge&logo=sqlalchemy&logoColor=white
[SQLAlchemy-url]: https://www.sqlalchemy.org/
[Poetry]: https://img.shields.io/badge/Poetry-4F5D95?style=for-the-badge&logo=poetry&logoColor=white
[Poetry-url]: https://python-poetry.org/

[Pytest]: https://img.shields.io/badge/pytest-008080?style=for-the-badge&logo=pytest&logoColor=white
[Pytest-url]: https://docs.pytest.org/
[Ruff]: https://img.shields.io/badge/ruff-000000?style=for-the-badge&logo=ruff&logoColor=white
[Ruff-url]: https://ruff.rs/
[Mypy]: https://img.shields.io/badge/mypy-4B8BBE?style=for-the-badge&logo=python&logoColor=white
[Mypy-url]: https://mypy.readthedocs.io/

[PostgreSQL]: https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white
[PostgreSQL-url]: https://www.postgresql.org/
[Docker]: https://img.shields.io/badge/docker-257bd6?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
[Docker Compose]: https://img.shields.io/badge/docker--compose-2496ed?style=for-the-badge&logo=docker&logoColor=white
[Docker Compose-url]: https://docs.docker.com/compose/
[GitHub Actions]: https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white
[GitHub Actions-url]: https://docs.github.com/en/actions
