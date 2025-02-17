import {
  makeStyles,
  tokens,
  typographyStyles
} from '@fluentui/react-components';

const DemoStyles = makeStyles({
  chatRoot: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%'
  },
  header: {
    zIndex: '50',
    height: '8vh',
    boxShadow: `0px 20px 17px 0px ${tokens.colorNeutralBackground1}`,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingLeft: tokens.spacingHorizontalL
  },
  actions: {
    display: 'flex',
    height: '32px',
    marginRight: tokens.spacingHorizontalL
  },
  exampleContainer: {
    flexGrow: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '100%'
  },
  chatContainer: {
    flexGrow: 1,
    display: 'flex',
    flexDirection: 'column',
    width: '100%'
  },
  chatEmptyState: {
    flexGrow: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center'
  },
  anonSwitch: {
    width: '240px'
  },
  chatEmptyStateTitle: typographyStyles.display,
  chatEmptyStateSubtitle: typographyStyles.subtitle1,

  // Styles for the mode toggle button
  modeButtons: {
    display: 'flex',
    justifyContent: 'center',
    width: '100%',
    paddingTop: tokens.spacingVerticalS,
    paddingBottom: tokens.spacingVerticalS,
  },
  modeButton: {
    alignSelf: 'center',
    marginTop: tokens.spacingVerticalXS,
    marginBottom: tokens.spacingVerticalS,
    marginLeft: '8px',
    ':hover': {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
});

export default DemoStyles;
