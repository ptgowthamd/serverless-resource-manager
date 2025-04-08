import React from 'react';
// import logo from './logo.svg'
import './App.css';
// import awsconfig from './aws-exports';
// import {AmplifySignOut, withAuthenticator } from '@aws-amplify/ui-react';
import { Amplify } from 'aws-amplify';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { CheckboxField } from '@aws-amplify/ui-react'
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
// import { withAuthenticator } from 'aws-amplify-react-native'

import awsExports from './aws-exports';
Amplify.configure(awsExports);

export default function App() {
return (
	<Authenticator
		// Default to Sign Up screen
		initialState="signUp"
		// Customize `Authenticator.SignUp.FormFields`
		components={{
			SignUp: {
				FormFields() {
					const { validationErrors } = useAuthenticator();
					return (
						<>
							{/* Re-use default `Authenticator.SignUp.FormFields` */}
							<Authenticator.SignUp.FormFields />

							{/* Append & require Terms & Conditions field to sign up  */}
							<CheckboxField
								errorMessage={validationErrors.acknowledgement}
								hasError={!!validationErrors.acknowledgement}
								name="acknowledgement"
								value="yes"
								label="I agree with the Terms & Conditions"
							/>
						</>
					);
				},
			},
		}}
		services={{
			async validateCustomSignUp(formData) {
				if (!formData.acknowledgement) {
					return {
						acknowledgement: 'You must agree to the Terms & Conditions',
					};
				}
			},
		}}
	>
		{({ signOut, user }) => (
			<main>
				<h1>Hello {user.signInDetails.loginId}</h1>
				<button onClick={signOut}>Sign out</button>
			</main>
		)}
	</Authenticator>
);
}