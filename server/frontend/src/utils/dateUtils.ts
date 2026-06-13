export const formatLastLogin = (lastLogin: Date | string | undefined) => {
  if (!lastLogin) {
    return 'Non disponible';
  }
  
  // Si lastLogin est une chaîne, on la convertit en objet Date
  const dateObject = lastLogin instanceof Date ? lastLogin : new Date(lastLogin);
  
  // Vérification que la date est valide
  if (isNaN(dateObject.getTime())) {
    return 'Date invalide';
  }
  
  return dateObject.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};
