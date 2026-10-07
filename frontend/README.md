# TaskFlow visual system

The application uses a local, precompiled Tailwind CSS 4.1.10 stylesheet.
No CDN, hosted font, frontend server, Node installation, or runtime CSS compiler
is required to run Django with this redesign.

## Editing the design later

From this directory:

```sh
npm install
npm run build
```

For development:

```sh
npm run watch
```

`input.css` is the source. The output is `../static/css/app.css`.
The compiler scans the project's templates and JavaScript. Both the source and
compiled file belong in version control. Do not commit `node_modules`.

- Layouts: `templates/layouts/`
- Reusable presentation: `templates/includes/`
- Mail HTML: `templates/emails/`
- Design tokens, surfaces and components: `input.css`
- Small UI interactions: `static/js/app.js`
- Existing task-status endpoint integration: `static/js/kanban.js`

The existing Django forms remain the source of truth for values, validation,
widgets and input names. Their `form-control` / `form-select` classes are styled
locally inside `.tf-form`; Bootstrap is not loaded.

## Sources

- Tailwind installation: https://tailwindcss.com/docs/installation/tailwind-cli
- Django HTML email: https://docs.djangoproject.com/en/6.1/topics/email/

Tailwind's MIT license is reproduced in `THIRD_PARTY_NOTICES.txt`.
No font files are bundled. The UI uses system fonts.
