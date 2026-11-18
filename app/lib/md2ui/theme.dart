// The shop's md2ui theme: THEME.md from backend/md2ui_theme (its MEANINGS.md and patterns
// are the agent's, never the app's), bundled with every face its `Font Name`s use by
// tool/sync_md2ui.sh under assets/md2ui/theme/, beside the page, so the view's Worker can
// load them. Keep this list and the files that script copies in step.

const md2uiTheme = {
  'src': 'theme/THEME.md',
  'fonts': [
    {'family': 'Plus Jakarta Sans', 'url': 'theme/assets/fonts/PlusJakartaSans-Medium.ttf', 'weight': 500},
    {'family': 'Plus Jakarta Sans', 'url': 'theme/assets/fonts/PlusJakartaSans-SemiBold.ttf', 'weight': 600},
    {'family': 'Plus Jakarta Sans', 'url': 'theme/assets/fonts/PlusJakartaSans-Bold.ttf', 'weight': 700},
    {'family': 'Plus Jakarta Sans', 'url': 'theme/assets/fonts/PlusJakartaSans-ExtraBold.ttf', 'weight': 800},
    {'family': 'Inter 18pt', 'url': 'theme/assets/fonts/Inter_18pt-Regular.ttf', 'weight': 400},
    {'family': 'Inter 18pt', 'url': 'theme/assets/fonts/Inter_18pt-Medium.ttf', 'weight': 500},
    {'family': 'Inter 18pt', 'url': 'theme/assets/fonts/Inter_18pt-SemiBold.ttf', 'weight': 600},
    {'family': 'Inter 18pt', 'url': 'theme/assets/fonts/Inter_18pt-Bold.ttf', 'weight': 700},
    // The theme's `## Emoji styles` Font, matched by URL: emoji draw as its icons.
    {'family': 'md2ui icons', 'url': 'theme/assets/icons/material-design-icons-md2ui.ttf'},
  ],
};
