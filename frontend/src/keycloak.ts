import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM ?? 'inquisitool',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? 'inquisitool-frontend',
});

export default keycloak;
