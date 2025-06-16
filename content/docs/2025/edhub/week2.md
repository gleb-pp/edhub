# EdHub Week 2 Report

<aside>

Capstone Project course

Innopolis University

June 2025

</aside>

# Plans & Prioritized backlog

We decided to split our project into several versions, each of which has full self-sufficient functionality. With each version new features are added to the project.

- **Materials**: Teacher can create courses, invite students, parents, or teachers, create materials. Student can enter the course and view the list of available materials. Parent can enter the course and view the list of available materials.
- **Assignment**: Teacher can create assignments, see the list of students' submissions and grade them. Student can submit assignments. Parents can track their students' submissions.
- **Files**: Teacher can attach files up to 5MB to course materials and assignments. Student can attach files up to 5MB to their submissions.

| Project Version | Backend | Frontend |
| --- | --- | --- |
| **Materials** | :ballot_box_with_check: Done in Week 1 | :white_check_mark: Done in Week 2 |
| **Assignment** | :white_check_mark: Done in Week 2 | :black_square_button: Planned for Week 3 |
| **Files** | :black_square_button: Planned for Week 3 | :black_square_button: Planned for Week 3 or Week 4 |

Since the project is dynamically changed, we plan to develop a detailed backlog at the beginning of each week. The backlog for Week 2 [was developed](https://github.com/orgs/IU-Capstone-Project-2025/projects/14/views/1) on June 12. The backlog for Week 3 will be extended after the meeting with TA.

# Individual contribution

### Gleb Popov
- [`backend`]: Backend part of the **Assignment** feature has been developed ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/21));
- [`backend`]: The feature of proper deletion of user account and all their data from the system has been developed ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/22));
- [`management`]: Project backlog with tasks for Week 2 has been created ([*kanban board*](https://github.com/orgs/IU-Capstone-Project-2025/projects/14/views/1)).
- [`management`]: A more detailed market research was carried out after the recommendation of TA ([**])
- [`management`]: Weekly report has been written ([*PR*](https://github.com/)).
<!-- add link for the pull request with weekly report -->

### Timur Usmanov
- [`backend`]: Docker network bug has been fixed after the recommendation of TA ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/6));
- [`backend`]: The correctness of input arguments of constraint checking functions is now validated ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/23));
- [`backend`]: Careful checking and commenting of pull request has been conducted ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/21), [*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/22)).

### Asqar Dinikeev
- [`devops`]: Project architecture has been developed, methods have been refactored into new modules ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/25)).

### Alina Suhoverkova
- [`frontend`]: 

### Timur Struchkov
- [`frontend`]: 

# Repository

[https://github.com/IU-Capstone-Project-2025/edhub](https://github.com/IU-Capstone-Project-2025/edhub)

We confirm that the code in the main branch:

- Is in working condition.
- Is runnable via `docker compose`.