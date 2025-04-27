/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  // Automatically clear mock calls, instances, contexts and results before every test
  clearMocks: true,
  // Setup files after env setup
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'], // Optional: if we need setup like importing jest-dom
  moduleNameMapper: {
    // Handle CSS imports (if any, e.g., from libraries)
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    // Handle module aliases (if configured in tsconfig.json)
    '^@/(.*)$': '<rootDir>/$1',
  },
  // Ignore node_modules, except for specific ones if needed (usually not)
  transformIgnorePatterns: [
    '/node_modules/',
    '^.+\\.module\\.(css|sass|scss)$', // Ignore CSS modules too if needed
  ],
  // Indicate that the coverage information should be collected while executing the test
  // collectCoverage: true,
  // The directory where Jest should output its coverage files
  // coverageDirectory: 'coverage',
  // An array of glob patterns indicating a set of files for which coverage information should be collected
  // collectCoverageFrom: [
  //   'app/**/*.{ts,tsx}',
  //   '!app/**/*.d.ts',
  //   '!app/**/layout.tsx', // Usually ignore layout files
  //   '!app/**/page.tsx', // Usually ignore top-level page files unless they have complex logic
  // ],
};
