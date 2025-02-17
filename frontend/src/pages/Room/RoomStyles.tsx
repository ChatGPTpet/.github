import { makeStyles, tokens, shorthands } from '@fluentui/react-components';

const RoomStyles = makeStyles({
  roomContainer: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%'
  },
  chatSection: {
    width: '100%',
    maxWidth: '800px',
    ...shorthands.border('1px solid gray'),
    ...shorthands.borderRadius('8px'),
    ...shorthands.overflow('hidden'),
    display: 'flex',
    flexDirection: 'column'
  },
  header: {
    zIndex: '50',
    height: '8vh',
    boxShadow: `0px 20px 17px 0px ${tokens.colorNeutralBackground1}`,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  headerTitle: {
    fontWeight: tokens.fontWeightSemibold,
    fontSize: tokens.fontSizeBase500,
    display: 'flex',
    alignItems: 'center'
  },
  actions: {
    display: 'flex',
    height: '32px',
    marginRight: tokens.spacingHorizontalL
  },
  emptyContainer: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    ...shorthands.gap(tokens.spacingHorizontalXL)
  },
  addIcon: {
    color: tokens.colorNeutralForeground4
  },
  bodyText: {
    color: tokens.colorNeutralForeground4
  },
  emptyAddFilesButton: {
    width: 'fit-content'
  },
  emptyTextContainer: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingHorizontalXS),
    alignItems: 'center'
  },
  anonSwitch: {
    width: '240px'
  },
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

export default RoomStyles;
