import { useTranslation } from 'react-i18next';import styles from './LanguageButton.module.css';
import { setLanguage } from '../../api';
import { useAuth0 } from "@auth0/auth0-react";

export const LanguageButton = ( ) => {
  const { i18n } = useTranslation();
  const { user, } = useAuth0();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  const handleClickLanguage = (newLanguage) => {
    // Hier kannst du den ausgewählten `newLanguage` verwenden, um die Sprache im Backend zu aktualisieren
    setLanguage({ language: newLanguage, auth0_id: user!.sub}) // Hier wird das ausgewählte newLanguage an setLanguage übergeben

    // Optional: Hier kannst du zusätzliche Aktionen ausführen, wenn die Sprache geändert wird
    changeLanguage(newLanguage);
  };

  return (
    <div className={styles['language-dropdown']}>
      <select onChange={(e) => handleClickLanguage(e.target.value)}>
        <option value="en">English</option>
        <option value="de">Deutsch</option>
      </select>
    </div>
  );
};
