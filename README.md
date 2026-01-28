[![Issues][issues-shield]][issues-url]
[![Stargazers][stars-shield]][stars-url]
[![Forks][forks-shield]][forks-url]
[![Unlicense License][license-shield]][license-url]

# What is EdHub?

EdHub is a Learning Management System designed to facilitate interaction among teachers, students, and parents. It enhances the educational process by simplifying communication between stakeholders and increasing student engagement in learning.

When developing EdHub, we focused on the following priorities:

- **Quick Start for Teachers**: Teachers can easily create a course by simply entering its title, invite students and their parents, upload learning materials, and create assignments.

- **Student Assignment Submissions**: Students can access course materials, submit their solutions to assignments, and receive grades from the teacher. Teachers can review submitted work, evaluate solutions, and provide grades.

- **Parental Access to Track Academic Progress**: Parents have a special role in EdHub. Once invited to a course, they can track their child's academic progress without having to ask for a student account or contact the teacher.

# Implementation Details

The project provides a fully functional REST API with a clean backend architecture,
well-defined API design, and clear separation of business logic.

*Note:* This repository currently focuses on the backend part of the system. The frontend is not included and is expected to be developed separately.

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

[![FastAPI][FastAPI]][FastAPI-url]
[![PostgreSQL][PostgreSQL]][PostgreSQL-url]
[![NginX][NginX]][NginX-url]
[![Docker][Docker]][Docker-url]

# Local Startup

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

## Contributing

EdHub is an open-source, non-commercial project developed primarily as a
portfolio and educational initiative and currently maintained by a single author.

### ⭐ Support the Project
If you find this project interesting or useful:
- Giving the repository a ⭐ star is very important and highly appreciated
- Following the author on GitHub helps support further development

Even small actions like these provide strong motivation to continue improving the project.

### 🐞 Bug Reports and Feedback
Bug reports, issue discussions, and general feedback are welcome.
If you notice unexpected behavior or have suggestions regarding usability
or documentation, feel free to open an issue.

### 🎨 Frontend Development
At the moment, the project does not include a production-ready frontend.
The previous frontend implementation was removed, and a new one is not yet available.

The backend API is fully functional and can be used as a foundation
for experimenting with frontend development, educational projects,
or personal portfolio work.

Please note that:
- The project is not commercial
- Frontend contributions are not paid
- Any frontend work would be driven by personal interest and portfolio goals

[contributors-shield]: https://img.shields.io/github/contributors/gleb-pp/edhub.svg?style=for-the-badge
[contributors-url]: https://github.com/gleb-pp/edhub/graphs/contributors
[stars-shield]: https://img.shields.io/github/stars/gleb-pp/edhub.svg?style=for-the-badge
[stars-url]: https://github.com/gleb-pp/edhub/stargazers
[forks-shield]: https://img.shields.io/github/forks/gleb-pp/edhub.svg?style=for-the-badge
[forks-url]: https://github.com/gleb-pp/edhub/network/members
[issues-shield]: https://img.shields.io/github/issues/gleb-pp/edhub.svg?style=for-the-badge
[issues-url]: https://github.com/gleb-pp/edhub/issues
[license-shield]: https://img.shields.io/github/license/gleb-pp/edhub.svg?style=for-the-badge
[license-url]: https://github.com/gleb-pp/edhub/blob/main/LICENSE
[prod-shield]: https://img.shields.io/github/actions/workflow/status/gleb-pp/edhub/deploy-prod.yml?style=for-the-badge
[prod-url]: https://github.com/gleb-pp/edhub/actions

[FastAPI]: https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi
[FastAPI-url]: https://fastapi.tiangolo.com/
[React]: https://img.shields.io/badge/-ReactJs-61DAFB?logo=react&logoColor=white&style=for-the-badge
[React-url]: https://react.dev/
[PostgreSQL]: https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white
[PostgreSQL-url]: https://www.postgresql.org/
[NginX]: https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white&style=for-the-badge
[NginX-url]: https://nginx.org/
[Docker]: https://img.shields.io/badge/docker-257bd6?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
