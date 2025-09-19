# Task Planning

This document outlines the standardized workflow for creating task plans in the QuantyFinAI Agent project.

## Plan Creation Workflow

### When to Create Plans

Create plan files in the following scenarios:
- When entering plan mode for feature implementation
- When creating structured todo lists for complex tasks
- When breaking down large tasks into manageable steps
- When documenting task requirements and specifications

### Plan Creation Process

1. **Check for existing date folder:** Look for folder with today's date (YYYY-MM-DD format)
2. **Create date folder if needed:** If folder doesn't exist, create it
3. **Create plan file:** Add the plan file inside the date folder
4. **Follow naming convention:** Use descriptive names without date prefix

### Plan File Management

**Location:** `/Users/tunganh252/Desktop/Study/AI101/quantyFin-ai-agent/vibeops/plans/tasks`

**Folder Structure:** 
- Create date folders in format `YYYY-MM-DD`
- Place plan files inside the corresponding date folder
- If date folder already exists, add plan file to that folder

**Naming Convention:** `name-of-task-or-name-of-plans.md` (without date prefix)

**File Path Examples:**
- `2025-09-16/user-authentication-implementation-plans.md`
- `2025-09-16/database-optimization-plans.md`
- `2025-09-16/api-endpoint-refactor-plans.md`
- `2025-09-17/new-feature-plans.md`

### Required Plan File Structure

Every plan file must begin with the following metadata:

```markdown
# Title: [Task/Feature Name]
**Status:** [Planning/In Progress/Completed/On Hold]
**Owner:** [Responsible Person/Team]
**Date Created:** [YYYY-MM-DD HH:MM:SS]
**Last Updated:** [YYYY-MM-DD HH:MM:SS]
**Priority:** [High/Medium/Low]

## Overview
[Brief description of the task/feature]

## Requirements
[Detailed requirements and specifications]

## Implementation Plan
[Step-by-step implementation plan]

## Dependencies
[List of dependencies and prerequisites]

## Success Criteria
[Definition of done and acceptance criteria]

## Original Plan
[Full plan]
```


## Directory Structure

```
vibeops/plans/tasks/
├── 2025-09-16/
│   ├── user-authentication-implementation-plans.md
│   ├── database-optimization-plans.md
│   └── api-endpoint-refactor-plans.md
├── 2025-09-17/
│   ├── new-feature-plans.md
│   └── bug-fix-plans.md
├── 2025-09-18/
│   └── performance-optimization-plans.md
└── drafts/
    ├── 2025-09-16-feature-a-drafts.md
    ├── 2025-09-16-feature-b-drafts.md
    └── ...
```

This workflow ensures consistent documentation, easy tracking of task progress, and comprehensive project history for future reference.