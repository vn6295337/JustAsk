module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/__tests__/**/*.test.js'],
  // Plain preset-env (babel.config.js uses babel-preset-expo, which is not
  // needed for these service-level tests)
  transform: {
    '\\.js$': [
      'babel-jest',
      { configFile: false, babelrc: false, presets: [['@babel/preset-env', { targets: { node: 'current' } }]] },
    ],
  },
  moduleNameMapper: {
    '^expo-sqlite$': '<rootDir>/src/__tests__/helpers/expoSqliteMock.js',
    '^expo-constants$': '<rootDir>/src/__tests__/helpers/expoConstantsMock.js',
    '^@react-native-community/netinfo$': '<rootDir>/src/__tests__/helpers/netinfoMock.js',
  },
};
