import styles from "./FileExplorer.module.css";
import {
  getTheme,
  mergeStyleSets,
  FontWeights,
  Text,
  Modal,
  IIconProps,
  Spinner
} from '@fluentui/react';
import { IconButton, IButtonStyles } from '@fluentui/react/lib/Button';
import { ArrowDownload24Regular, Folder24Regular } from '@fluentui/react-icons';
import { getDocuments, deleteDocuments, reloadFiles } from '../../api';
import { TextField } from '@fluentui/react/lib/TextField';
import { ReadDocument } from '../../api';
import { TooltipHost, DefaultButton } from '@fluentui/react';
import { Announced } from '@fluentui/react/lib/Announced';
import { DetailsList, DetailsListLayoutMode, Selection, SelectionMode, IColumn } from '@fluentui/react/lib/DetailsList';
import * as React from 'react';
import { User } from "@auth0/auth0-react";
import { withTranslation } from "react-i18next";

const classNames = mergeStyleSets({
  fileIconHeaderIcon: {
    padding: 0,
    fontSize: '16px',
  },
  fileIconCell: {
    textAlign: 'center',
    selectors: {
      '&:before': {
        content: '.',
        display: 'inline-block',
        verticalAlign: 'middle',
        height: '100%',
        width: '0px',
        visibility: 'hidden',
      },
    },
  },
  fileIconImg: {
    verticalAlign: 'middle',
    maxHeight: '16px',
    maxWidth: '16px',
  },
  controlWrapper: {
    display: 'flex',
    flexWrap: 'wrap',
  },
  exampleToggle: {
    display: 'inline-block',
    marginBottom: '10px',
    marginRight: '30px',
  },
  selectionDetails: {
    marginBottom: '20px',
  },
});
const controlStyles = {
  root: {
    margin: '0 30px 20px 0',
    maxWidth: '300px',
  },
};

export interface FileExplorerState {
  columns: IColumn[];
  items: ReadDocument[];
  initialItems: ReadDocument[];
  selectionDetails: string;
  isModalSelection: boolean;
  isCompactMode: boolean;
  announcedMessage?: string;
  modalState: boolean;
  isLoading: boolean;
  isReloading: boolean;
}
class FileExplorer extends React.Component<{ user: User, t: any }, FileExplorerState> {
  private _selection: Selection;



  constructor(props: { user: User, t: any }) {
    super(props);

    const columns: IColumn[] = [
      {
        key: 'column1',
        name: 'File Type',
        className: classNames.fileIconCell,
        iconClassName: classNames.fileIconHeaderIcon,
        ariaLabel: 'Column operations for File type, Press to sort on File type',
        iconName: 'Page',
        isIconOnly: true,
        fieldName: 'name',
        minWidth: 16,
        maxWidth: 16,
        onColumnClick: this._onColumnClick,
        onRender: (item: ReadDocument) => {
          const filename = item.filename;
          const fileExtension = filename.split('.').pop();
          const file_icon = `https://res-1.cdn.office.net/files/fabric-cdn-prod_20230815.002/assets/item-types/16/${fileExtension}.svg`

          return (
            <TooltipHost content={`${fileExtension} file`}>
              <img src={file_icon} className={classNames.fileIconImg} alt={`${fileExtension} file icon`} />
            </TooltipHost>
          );
        },
      },
      {
        key: 'column2',
        name: 'Name',
        className: styles.file_name_column,
        fieldName: 'filename',
        minWidth: 500,
        isRowHeader: true,
        isResizable: true,
        isSorted: true,
        isSortedDescending: false,
        sortAscendingAriaLabel: 'Sorted A to Z',
        sortDescendingAriaLabel: 'Sorted Z to A',
        onColumnClick: this._onColumnClick,
        data: 'string',
        isPadded: true,
      },
      {
        key: 'column3',
        name: 'Download',
        className: styles.file_name_column,
        fieldName: 'download',
        minWidth: 50,
        isRowHeader: true,
        isResizable: true,
        data: 'string',
        isPadded: true,
        onRender: (item: ReadDocument) => {
          const encodedFilename = encodeURIComponent(item.filename);
          const file_path = `/api/documents/download/${encodedFilename}`
        
          return (
            <a href={file_path} download>
              <ArrowDownload24Regular/>
            </a>
          );
        },
      },
      {
        key: 'column4',
        name: this.props.t('fileSize'),
        className: styles.file_name_column,
        fieldName: 'fileSize',
        minWidth: 100,
        isRowHeader: true,
        isResizable: true,
        data: 'number',
        isPadded: true,
        onRender: (item: ReadDocument) => {
          const fileSizeInMB = item.fileSize / (1024 * 1024);
          let sizeText = "";
        
          if (fileSizeInMB < 1) {
            sizeText = `${(item.fileSize / 1024).toFixed(0)} KB`;
          } else if (fileSizeInMB >= 1024) {
            sizeText = `${(fileSizeInMB / 1024).toFixed(2)} GB`;
          } else {
            sizeText = `${fileSizeInMB.toFixed(2)} MB`;
          }
        
          return (            
            <span>{sizeText}</span>
          );
        },
      }
    ];

    this._selection = new Selection({
      onSelectionChanged: () => {
        this.setState({
          selectionDetails: this._getSelectionDetails(),
        });
      },
      getKey: this._getKey,
    });

    this.state = {
      items: [],
      initialItems: [],
      columns,
      selectionDetails: this._getSelectionDetails(),
      isModalSelection: true,
      isCompactMode: false,
      announcedMessage: undefined,
      modalState: false,
      isLoading: true,
      isReloading: false
    };
  }

  public render() {
    const { columns, isCompactMode, items, selectionDetails, isModalSelection, announcedMessage, modalState } = this.state;
    const currentURL = window.location.pathname;

    return (
      <div>
        <div className={`${styles.container} ${styles.commandButton ?? ""}`} onClick={this._showModal}>
          <Folder24Regular />
          <Text>{this.props.t('files')}</Text>
        </div>
        <Modal
          isOpen={modalState}
          onDismiss={() => {
            this._hideModal;
          }}
          isBlocking={false}
          containerClassName={contentStyles.container}
        >
          <div className={contentStyles.header}>
            <h2 className={contentStyles.heading} id={"fileExplorer"}>
              {this.props.t('uploadedFiles')}
            </h2>
            <IconButton
              styles={iconButtonStyles}
              iconProps={cancelIcon}
              ariaLabel="Close popup modal"
              onClick={this._hideModal}
            />
          </div>
          <div className={styles.modal_container}>
            <div className={styles.modal_navigation}>
              <div className={classNames.controlWrapper}>
                <TextField label={this.props.t('filterByName')} onChange={this._onChangeText} styles={controlStyles} />
                <Announced message={`Number of items after filter applied: ${items.length}.`} />
              </div>
              <div className={styles.actionButtons}>
                {currentURL !== '/demo' && currentURL !== '/#/demo' && (
                  <>
                    <DefaultButton
                      text={this.props.t('deleteDoc')}
                      className={styles.btn_danger}
                      onClick={this._handleDeleteClick}
                    />
                    <DefaultButton
                      text={this.props.t('reloadDoc')}
                      onClick={this._reloadFiles}
                    />
                  </>
                )}
                {this.state.isReloading && (
                  <Spinner label={this.props.t('reloading')} ariaLive="assertive" labelPosition="right" />
                )}
              </div>
            </div>
            <div className={classNames.selectionDetails}>{selectionDetails}</div>
            <Announced message={selectionDetails} />
            {announcedMessage ? <Announced message={announcedMessage} /> : undefined}
            <DetailsList
              items={items}
              columns={columns}
              className={styles.details_list}
              selectionMode={SelectionMode.multiple}
              setKey="multiple"
              layoutMode={DetailsListLayoutMode.justified}
              isHeaderVisible={true}
              selection={this._selection}
              selectionPreservedOnEmptyClick={true}
              enterModalSelectionOnTouch={true}
              ariaLabelForSelectionColumn="Toggle selection"
              ariaLabelForSelectAllCheckbox="Toggle selection for all items"
              checkButtonAriaLabel="select row"
              onItemInvoked={this._onItemInvoked}
            />
          </div>
        </Modal >
      </div >
    );
  };

  private _onItemInvoked(item: any): void {
    console.log(item)
  }


  public componentDidUpdate(previousProps: any, previousState: FileExplorerState) {
    if (previousState.isModalSelection !== this.state.isModalSelection && !this.state.isModalSelection) {
      this._selection.setAllSelected(false);
    }
  }

  private _getKey(item: any, index?: number): string {
    return item.key;
  }

  private _showModal = (ev: React.MouseEvent<HTMLElement>): void => {
    this.setState({ modalState: true });
    getDocuments(this.props.user.sub!).then((response) => {
      this.setState({ items: response, initialItems: response, isLoading: false })
    });
  };

  private _hideModal = (ev: React.MouseEvent<HTMLElement>): void => {
    this.setState({ modalState: false, items: [], initialItems: [] })
  };


  private _onChangeText = (ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, text?: string): void => {
    const { initialItems } = this.state;
    this.setState({
      items: text ? initialItems.filter(i => i.filename.toLowerCase().includes(text.toLowerCase())) : initialItems,
    });
  };

  private _handleDeleteClick = () => {
    const selectedItems = this._selection.getSelection() as ReadDocument[];

    if (selectedItems.length > 0) {
      // Call the deleteDocuments function with selected items
      deleteDocuments(selectedItems)
        .then(() => {
          // Remove the deleted items from the state
          this.setState((prevState) => ({
            items: prevState.items.filter((item) => !selectedItems.includes(item)),
          }));
          // Clear the selection
          this._selection.setAllSelected(false);
        })
        .catch((error) => {
          console.error('Error deleting documents:', error);
        });
    }
  };

  private _reloadFiles = () => {
    const auth0_id = this.props.user.sub!;
    this.setState(() => ({ isReloading: true }))
    // Call the deleteDocuments function with selected items
    reloadFiles(auth0_id)
      .then(() => {
        this.setState(() => ({ isReloading: false }))
      })
      .catch((error) => {
        this.setState(() => ({ isReloading: false }))
        console.error('Error deleting documents:', error);
      });

  };

  private _onColumnClick = (ev: React.MouseEvent<HTMLElement>, column: IColumn): void => {
    const { columns, items } = this.state;
    const newColumns: IColumn[] = columns.slice();
    const currColumn: IColumn = newColumns.filter(currCol => column.key === currCol.key)[0];
    newColumns.forEach((newCol: IColumn) => {
      if (newCol === currColumn) {
        currColumn.isSortedDescending = !currColumn.isSortedDescending;
        currColumn.isSorted = true;
        this.setState({
          announcedMessage: `${currColumn.name} is sorted ${currColumn.isSortedDescending ? 'descending' : 'ascending'
            }`,
        });
      } else {
        newCol.isSorted = false;
        newCol.isSortedDescending = true;
      }
    });
    const newItems = _copyAndSort(items, currColumn.fieldName!, currColumn.isSortedDescending);
    this.setState({
      columns: newColumns,
      items: newItems,
    });
  };

  private _getSelectionDetails(): string {
    const selectionCount = this._selection.getSelectedCount();

    switch (selectionCount) {
      case 0:
        return this.props.t('noSelectedItems');
      case 1:
        return this.props.t('selectedItems') + (this._selection.getSelection()[0] as ReadDocument).filename;
      default:
        return `${selectionCount}` + this.props.t('selectedMoreItems');
    }
  }
}

export default withTranslation()(FileExplorer);


function _copyAndSort<T>(items: T[], columnKey: string, isSortedDescending?: boolean): T[] {
  const key = columnKey as keyof T;
  return items.slice(0).sort((a: T, b: T) => ((isSortedDescending ? a[key] < b[key] : a[key] > b[key]) ? 1 : -1));
}

const cancelIcon: IIconProps = { iconName: 'Cancel' };

const theme = getTheme();
const contentStyles = mergeStyleSets({
  container: {
    display: 'flex',
    flexFlow: 'column nowrap',
    alignItems: 'stretch',
    width: '75%'
  },
  header: [
    // eslint-disable-next-line deprecation/deprecation
    theme.fonts.xLargePlus,
    {
      flex: '1 1 auto',
      borderTop: `4px solid ${theme.palette.themePrimary}`,
      color: theme.palette.neutralPrimary,
      display: 'flex',
      alignItems: 'center',
      fontWeight: FontWeights.semibold,
      padding: '12px 12px 14px 24px',
    },
  ],
  heading: {
    color: theme.palette.neutralPrimary,
    fontWeight: FontWeights.semibold,
    fontSize: 'inherit',
    margin: '0',
  },
  body: {
    grid: '4 4 auto',
    padding: '0 24px 24px 24px',
    overflowY: 'hidden',
    selectors: {
      p: { margin: '14px 0' },
      'p:first-child': { marginTop: 0 },
      'p:last-child': { marginBottom: 0 },
    },
  },
  textfield: {
    width: '100%'
  }
});
const iconButtonStyles: Partial<IButtonStyles> = {
  root: {
    color: theme.palette.neutralPrimary,
    marginLeft: 'auto',
    marginTop: '4px',
    marginRight: '2px',
  },
  rootHovered: {
    color: theme.palette.neutralDark,
  },
};