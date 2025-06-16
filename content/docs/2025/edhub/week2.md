# EdHub Week 2 Report

<aside>

Capstone Project course

Innopolis University

June 2025

</aside>

# Weekly achievments

## Market Research

After a meeting with TA on June 12, we were recommended to conduct a more detailed market analysis of similar products to identify useful features we want to implement in our project and gaps we want to fill.

#### Google Classroom

**Advantages (what we wnat to take):**

- user-friendly design
- easy and quick setup (every user can create a course in 1 minute)
- easy customization of criteria for each task
- completely free functionality

**Disadvantages (what we wnat to fix):**

- no parental access
- no support for course evaluation in general
- no attendance tracking mechanism
- no local hosting option (for data secutiry)

#### Moodle LMS

**Advantages (what we wnat to take):**

- attendance tracking mechanism
- flexible customization of the course evaluation formula
- completely free functionality

**Disadvantages (what we wnat to fix):**

- сomplexity of setup (requires configuration at the organization level)
- no parental access
- no global servers (you always have to host your own)
- a lot of unnecessary functionality that complicates the design
- no customization of criteria for evaluating assignments

#### Stepik

**Advantages (what we wnat to take):**

- user-friendly design
- easy and quick setup
- easy customization of criteria for each task

**Disadvantages (what we wnat to fix):**

- restrictions on course creation (at least 1 module and at least 9 lessons **must be** created)
- no parental access
- no attendance tracking mechanism
- no local hosting option (for data secutiry)
- paid invitation of additional teachers
- paid attachments upload
- paid student report card

## Management: Plans & Prioritized backlog

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

## Backend

## Frontend

# Individual contribution

### Gleb Popov
- [`management`]: A more detailed market research was carried out after the recommendation of TA ([**])
- [`management`]: Project backlog with tasks for Week 2 has been created ([*kanban board*](https://github.com/orgs/IU-Capstone-Project-2025/projects/14/views/1)).
- [`management`]: Weekly report has been written ([*PR*](https://github.com/)).
- [`backend`]: Backend part of the **Assignment** feature has been developed ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/21));
- [`backend`]: The feature of proper deletion of user account and all their data from the system has been developed ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/22));
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