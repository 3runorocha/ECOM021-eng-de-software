import { createContext, useContext } from 'react'

// O contexto e o hook moram aqui, separados do componente, porque o
// fast-refresh do React so funciona em arquivo que exporta apenas componentes.
export const AuthContext = createContext(null)

export const useAuth = () => useContext(AuthContext)
