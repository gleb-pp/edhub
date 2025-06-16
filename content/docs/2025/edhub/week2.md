# EdHub Week 2 Report

<aside>

Capstone Project course

Innopolis University

June 2025

</aside>

# Weekly achievments

## Market Research

After a meeting with TA on June 12, we were recommended to conduct a more detailed market analysis of similar products to identify useful features we want to implement in our project and gaps we want to fill.

We analyzed the 3 popular LMSs (Google Classroom, Moodle, and Stepik) and concluded that none of them are suitable for quick setup and easy use by school teachers. Based on the market, we wrote out the functionality of EdHub and compared it with existing solutions:

- **user-friendly design** (implemented in Google Classroom and Stepik, Moodle is hard to evaluate)
- **easy and quick setup** (implemented in Google Classroom, lacking in Stepik and Moodle)
- **easy customization of criteria for each task** (implemented in Google Classroom and Stepik, lacking in Moodle)
- **completely free functionality** (implemented in Google Classroom and Moodle, lacking in Stepik)
- **parental access** (lacking in Google Classroom, Moodle, and Stepik)
- **flexible customization of the course evaluation formula** (implemented in Moodle and Stepik, lacking in Google Classroom)
- **attendance tracking mechanism** (implemented in Moodle, lacking in Google Classroom and Stepik)
- **global servers** (implemented in in Google Classroom and Stepik, lacking in Moodle)
- **local hosting option** (implemented in Moodle, lacking in Google Classroom and Stepik)

## Plans & Prioritized backlog

We decided to split our project into several versions, each of which has full self-sufficient functionality. With each version new features are added to the project.

- **Materials**: Teacher can create courses, invite students, parents, or teachers, create materials. Student can enter the course and view the list of available materials. Parent can enter the course and view the list of available materials.
- **Assignment**: Teacher can create assignments, see the list of students' submissions and grade them. Student can submit assignments. Parents can track their students' submissions.
- **Files**: Teacher can attach files up to 5MB to course materials and assignments. Student can attach files up to 5MB to their submissions.

By the end of Week 3, we plan to have an MVP of our product, and the global plan for the week is the following:

| Project Version | Backend | Frontend |
| --- | --- | --- |
| **Materials** | :ballot_box_with_check: Done in Week 1 | :white_check_mark: Done in Week 2 |
| **Assignment** | :white_check_mark: Done in Week 2 | :black_square_button: Planned for Week 3 |
| **Files** | :black_square_button: Planned for Week 3 | :black_square_button: Planned for Week 3 or Week 4 |

During the development process we sometimes change the vision of our product, so we plan to focus on a more detailed backlog and work out the week's plan at the beginning of each week. The backlog for Week 2 [was developed](https://github.com/orgs/IU-Capstone-Project-2025/projects/14/views/1) on June 12. The backlog for Week 3 will be extended after the meeting with TA and discussing the project.

## Backend

The main task of the backend team this week was to work on the API commands to implement the **assignments and grades feature**. A teacher can now create assignments within a course and add a title and description to them. Students can attach their text responses to assignments and submit them to the teacher for review. The teacher can track student submissions and grade them. Parents of students can also track their children's submissions.

We also found that there is no way for a user to **delete their account** on the site. We consider the user's right to delete their account and all data about themselves from the service to be a priority, so we have implemented such an option.

During the review of the account deletion function poolquest, we came up with the idea of not deleting all user-related data directly using sql queries, but rather **writing `on delete` functions** into the database initialization script. This way PostrgreSQL will automatically process user data when deleting a user from the `users` table. We also decided to apply this solution to improve the `remove_course` function, which previously had to delete all students, materials, and other related data manually.

We also need to check the correctness of the input data before handling the request. For example, when we receive a request to add a student to a course, we call: 

1. a function to check that the course exists
2. a function to check that the invited user exists
3. a function to check that the user is not already a member of that course
4. a function to check that the sender of the request has teacher privileges

This week we realized that some of these checks overlap and **removed the unnecessary ones** to speed up the processing of requests. For example, we don't need to call the check 2, because this check is implemented within the check 3, which also validates the input parameters.

## Frontend



## DevOps

After the TA's recommendation, we fixed the network settings in the `docker-compose.yml` file that previously specified a concrete address.

We also decided to redesign the architecture of the project to break one big `main.py` file into several parts with logic, models and routers. This way the project will be more scalable and it will be easier to work on several functions in parallel.

## Plan for the Week 3

During the Week 3, we plan to fully finalize the MVP of our project: the frontend team will create pages for assignments with their descriptions and the ability to submit students' work. The backend team will work on the ability to attach files to materials and assignments. If the frontend team has time left, they will also develop a frontend for uploading files.

# Individual contribution

### Gleb Popov
- [`backend`]: Backend part of the **Assignment** feature has been developed ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/21));
- [`backend`]: The feature of proper deletion of user account and all their data from the system has been developed ([*PR*](https://github.com/IU-Capstone-Project-2025/edhub/pull/22));
- [`management`]: A more detailed market research was carried out after the recommendation of TA;
- [`management`]: Development plan and weekly backlog have been created ([*kanban board*](https://github.com/orgs/IU-Capstone-Project-2025/projects/14/views/1));
- [`management`]: Weekly report has been written ([*PR*](https://github.com/IU-PR/Capstone_project/pull/493)).
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