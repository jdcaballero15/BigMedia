import { configure } from '@testing-library/react'

// Más margen para findBy/waitFor: con la cobertura y la CPU cargada, 1 s a veces no alcanza.
configure({ asyncUtilTimeout: 3000 })
