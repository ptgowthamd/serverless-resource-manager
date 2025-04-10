# Project setup:

> Go to directory where you want to create your reactjs project and install amplify cli. (One time installation)

```bash
npm install -g @aws-amplify/cli
```

> Create react-app

```bash
npx create-react-app test-project
```

```bash
cd test-project<project-name>
```
(go to your react-app project directory) and  
run app (Starts the development server) with  
```bash
npm start
```
to test  
Ctrl + c to Terminate running app (dev server)

> Configure AWS IAM user for amplify to set up project AWS resources (If configured IAM user has enough permissions, you can skip this step)

```bash
amplify configure
```

Note: If it's failed with error like unauthorizedaccess to run .ps1 script. Then you can open powershell with Adminstrator access & run cmd  
```bash
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted
```

It takes you to a default browser to login to AWS account with your credentials.

Select required region:

Specify username of the new IAM user: `<user-name>` enter  
Again it takes to default browser to IAM user creation page. It's fine to create user with suggested permissions.  
Download credentials .csv file

Back to VisualStudio:  
give access-key, secret-key of new IAM user created and give profile name. This will create/update the AWS Profile in your local machine (file `.aws/credentials`)

> Initialize amplify project to get boilerplate code & config for project setup for frontend and backend (AWS resources config). And create deployment S3 bucket (like backend infra) and  
a couple of IAM roles (auth and unauth roles used to create temporary credentials to access cognito-identity and another role to deny to access cognito-identity)  
`[cognito-identity.amazonaws.com]`

```bash
amplify init
```
(Note: It is recommended to run this command from the root of your app directory)

Enter Name of the Project:

Confirm to Initialize the project with the displayed configuration. (Uses CloudFormation as a default provider)

Select authentication methods you want to use? (aws-profile/aws-accesskeys)  
(it's easy to choose profile-name created in local for this new IAM user)

> Add Authentication to our front-end application using AWS Cognito

```bash
amplify add auth
```

Select "Manual configuration"

Select "User Sign-Up & Sign-In only (Best used with a cloud API only)"

Give label for the resources of this project

Give name of the user pool: `test-userpool<user-pool name>`

Select "Email" for users able to sign in with.

Select "No" for adding user pool groups.

Select "No" for adding an admin queries API.

Select "Optional (Individual users can use MFA)" for "MFA options"

Select "Time-Based One-Time Password" (TOTP) for "MFA types"

we can keep default for "SMS authentication message"

Select "Enabled (Requires per-user email entry at registration)" for "Email based registration/forgot password"

we can keep default subject for "email verification subject"

we can keep default message for "email verification message"

No for "override default password policy for this user pool"  
Just keep "Email" attribute for required attribute for sign-up

we can keep default expiration period for "the app's refresh token expiration period"

No for "specify user attributes this app can read and write?"

No opt's for "enable any of the following capabilities?" (It's good to enable google recaptcha but need to register to Google reCAPTHA site)

No for "OAuth flow?"

No for "Lambda Triggers for Cognito?"

> Add serverless rest-api with cognito-authorizer:

The `amplify add api` command asks to choose REST or GraphQL, choose REST

✔ Provide a friendly name for your resource to be used as a label for this category in the project: `testapi`  
✔ Provide a path (e.g., /book/{isbn}): `· /user`  
✔ Choose a Lambda source  
  Create a new Lambda function  
   Use a Lambda function already added in the current Amplify project

choose "Create a new Lambda function"

  ? Provide an AWS Lambda function name: `testLambdaFunction`  
  ? Choose the runtime that you want to use: `NodeJS`  
  ? Choose the function template that you want to use: `Hello World`

Available advanced settings:
- Resource access permissions
- Scheduled recurring invocation
- Lambda layers configuration
- Environment variables configuration
- Secret values configuration

  ? Do you want to configure advanced settings? **No**  
  ? Do you want to edit the local lambda function now? **Yes**  
  Edit the file in your editor: `/amplify/backend/function/testLambdaFunction/src/index.js`  
  ? Press enter to continue  
  Successfully added resource `testLambdaFunction` locally.

  ✅ Succesfully added the Lambda function locally  
  ✔ Restrict API access? (Y/n) · **no**  
  ✔ Do you want to add another path? (y/N) · **no**  
  ✅ Successfully added resource `testapi` locally

>>> Use override rest-api to add cognito-authorizer (as of now "amplify cli" doesn't cognito-authorizer for serverless-rest-api)

```bash
amplify override api
```

  ✅ Successfully generated `override.ts` folder at `/Users/gowthamd/Training/DevOps/Amplify Test/amplify-fullstackapp-test/amplify/backend/api/testrestapi`  
  ✔ Do you want to edit override.ts file now? (Y/n) · **yes**

  Add the below overriding configuration for API-Gateway:API

```typescript
// This file is used to override the REST API resources configuration
import { AmplifyApiRestResourceStackTemplate } from '@aws-amplify/cli-extensibility-helper';

export function override(resources: AmplifyApiRestResourceStackTemplate) {
    // Override API name
    resources.restApi.addPropertyOverride("Name", {
        "Fn::Join": [
            "",
            [
                "useractivity",
                "-",
                {
                    "Ref": "env"
                }
            ]
        ]
    });

    // Add a parameter to your Cloud Formation Template for the User Pool's ID
    resources.addCfnParameter({
        type: "String",
        description: "The id of an existing User Pool to connect. If this is changed, a user pool will not be created for you.",
        default: "NONE",
    },
        "AuthCognitoUserPoolId",
        { "Fn::GetAtt": ["authtestuserpool", "Outputs.UserPoolId"], }
    );

    // Create the authorizer using the AuthCognitoUserPoolId parameter defined above
    resources.restApi.addPropertyOverride("Body.securityDefinitions", {
        Cognito: {
            type: "apiKey",
            name: "Authorization",
            in: "header",
            "x-amazon-apigateway-authtype": "cognito_user_pools",
            "x-amazon-apigateway-authorizer": {
                type: "cognito_user_pools",
                providerARNs: [
                    { 'Fn::Sub': 'arn:aws:cognito-idp:${AWS::Region}:${AWS::AccountId}:userpool/${AuthCognitoUserPoolId}' },
                ],
            },
        },
    });

    // For every path in our REST API
    for (const path in resources.restApi.body.paths) {
        // Add the Authorization header as a parameter to requests
        resources.restApi.addPropertyOverride(
            `Body.paths.${path}.x-amazon-apigateway-any-method.parameters`,
            [
                ...resources.restApi.body.paths[path]["x-amazon-apigateway-any-method"]
                    .parameters,
                {
                    name: "Authorization",
                    in: "header",
                    required: false,
                    type: "string",
                },
            ]
        );
        // Use our new Cognito User Pool authorizer for security
        resources.restApi.addPropertyOverride(
            `Body.paths.${path}.x-amazon-apigateway-any-method.security`,
            [{ Cognito: [], },]
        );
    }
}
```

> Create/Update the cloud resources

```bash
amplify push
```
(Which creates cognito-user-pool with given spec, required lambda functions and roles to work on this cognito-user-pool)

Yes to continue.

> Install Amplify UI library for reactjs

```bash
npm install --save aws-amplify @aws-amplify/ui-react
```

> Edit App.js as required (to integrate with CognitoAuthentication before go to landing-page)

```javascript
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
          <h1>Hello {user.username}</h1>
          <button onClick={signOut}>Sign out</button>
        </main>
      )}
    </Authenticator>
  );
}
```

> Start development server

```bash
npm start
```

> amplify hosting add

> amplify publish

  >> Choose "Amplify managed website hosting"  
  >> Choose "Manually uploaded code"

---

Note:

Amplify push for Infra and backend code deployment  
Amplify publish for FE Infra and code deployment
