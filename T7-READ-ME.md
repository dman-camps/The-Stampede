# T7: Search and filtering

These files add search and filtering to the existing Stampede project. It is not a complete standalone project.

## Features

- Search event titles and descriptions.
- Filter by category, date, location, maximum cost, and available spaces.
- Combine or clear filters.
- Choose a category when creating an event.

Search results require a verified account. Invalid search values show form errors.

## Setup

Merge the supplied files into the team's project, keeping any newer team changes. Back up your database first if needed.

With the project's environment activated and configured, run:

```powershell
python manage.py migrate
python manage.py test stamps
python manage.py runserver
```

## Changed files

- `stamps/models.py` and `stamps/migrations/0007_stamp_category.py`: add categories; existing events default to Other.
- `stamps/forms.py`: search fields and event category selection.
- `stamps/home_views.py`: search and filter logic.
- `stamps/templates/stamps/home.html` and `stamps/static/stamps/styles.css`: filter controls and styling.
- `stamps/test_t7.py`: six basic tests for search, filters, combined filters, invalid input, access, and category saving.
- `stamps/tests.py`: only adds `category='study'` to an existing event-creation test submission.

## Testing

All 25 tests passed: 19 existing tests and 6 T7 tests.
