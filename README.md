# Open World Mission Hub

## Problem Statement

Build a backend application inspired by open-world games. Players can explore available missions, accept missions, complete objectives, and earn rewards. Administrators manage the platform, while mission managers create missions and validate completion.

*(Backend only)*

## User Roles

| Role | Responsibilities | 
| ----- | ----- | 
| **Admin** | Manage mission managers and platform activities | 
| **Mission Manager** | Create missions, manage availability, and verify completion | 
| **Player** | Accept missions, submit completion details, and earn rewards | 

* New registrations receive the `player` role by default.

* Only admins can create mission manager accounts.

## Business Rules & Reward System

* A mission must contain a **title**, **description**, **difficulty**, **location**, and **reward**.

* Missions can have difficulty levels such as `easy`, `medium`, and `hard`.

* Mission managers can publish and deactivate missions.

* Players can accept available missions.

* A player cannot accept the same active mission more than once.

* Players must submit completion details before a mission can be marked completed.

* Mission managers must approve or reject submitted completion details.

* Rewards can be assigned only after successful completion.

* Players must have a profile showing completed missions, total rewards, and experience points.

* The leaderboard must rank players based on accumulated experience points.

* The backend must calculate rewards based on approved mission completion.

| Mission Difficulty | Experience Points | 
| ----- | ----- | 
| Easy | 50 | 
| Medium | 100 | 
| Hard | 200 | 
| Special | 500 | 

## API Contracts (18 Total)

### A. Authentication APIs (3)

| \# | Functionality | Method | Endpoint | Request Body | Response | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| **A1** | Register a new account | `POST` | `/auth/register` |  |  | 
| **A2** | Login and generate access and refresh tokens | `POST` | `/auth/login` |  |  | 
| **A3** | Generate a new access token | `POST` | `/auth/refresh` |  |  | 

### B. Project-Specific APIs (15)

| \# | Functionality | Access | Method | Endpoint | Request Body | Response | 
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | 
| **E1** | Create a mission manager account | Admin |  |  |  |  | 
| **E2** | Create a new mission | Mission Manager |  |  |  |  | 
| **E3** | Get all available missions | All |  |  |  |  | 
| **E4** | Get details of a particular mission | All |  |  |  |  | 
| **E5** | Update mission details or availability | Mission Manager |  |  |  |  |
| **E6** | Accept a mission | Player | POST | /missions/{mission_id}/accept | | |
| **E7** | Get missions accepted by the logged-in player | Player | GET | /players/me/missions/active | | |
| **E8** | Submit mission completion details | Player | POST | /missions/{mission_id}/submit | | |
| **E9** | Approve or reject a mission completion | Mission Manager | PATCH | /submissions/{submission_id}/review | | |
| **E10** | Get a player's completed mission history | Player | GET | /players/me/missions/completed | | |
| **E11** | Create a reward for a mission | Mission Manager | POST | /rewards | {"name": "string","mission_id": 0} | |
| **E12** | Get available rewards | All | GET | /rewards | | |
| **E13** | Assign a reward to a player | Mission Manager | POST | /rewards/{reward_id} | | |
| **E14** | Get player rankings and leaderboard | All | GET | /leaderboard | | |
| **E15** | Get player profile and statistics | All | GET | /stats/{user_id} |  |  | 

## Database Tables (To Be Designed)

| Table Name | Fields | Constraints / Relationships | 
| ----- | ----- | ----- | 
|  |  |  | 
|  |  |  | 
|  |  |  | 
|  |  |  | 
|  |  |  | 

## Development Tracker

| API # | Functionality | Assigned To | Status | 
| ----- | ----- | ----- | ----- | 
| **A1** | Register a new account |  |  | 
| **A2** | Login and generate access and refresh tokens |  |  | 
| **A3** | Generate a new access token |  |  | 
| **E1** | Create a mission manager account |  |  | 
| **E2** | Create a new mission |  |  | 
| **E3** | Get all available missions |  |  | 
| **E4** | Get details of a particular mission |  |  | 
| **E5** | Update mission details or availability |  |  |
| **E6** | Accept a mission | Soham | Complete |
| **E7** | Get missions accepted by the logged-in player | Soham | ✅ |
| **E8** | Submit mission completion details | Soham | ✅ |
| **E9** | Approve or reject a mission completion | Soham | ✅ |
| **E10** | Get a player's completed mission history | Soham | ✅ |
| **E11** | Create a reward for a mission | Shafi | ✅ |
| **E12** | Get available rewards | Shafi | ✅ |
| **E13** | Assign a reward to a player | Shafi | ✅ |
| **E14** | Get player rankings and leaderboard | Shafi | ✅ |
| **E15** | Get player profile and statistics | Shafi |✅ |
