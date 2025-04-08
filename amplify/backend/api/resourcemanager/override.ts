// This file is used to override the REST API resources configuration
import { AmplifyApiRestResourceStackTemplate, AmplifyProjectInfo } from '@aws-amplify/cli-extensibility-helper';

export function override(resources: AmplifyApiRestResourceStackTemplate, amplifyProjectInfo: AmplifyProjectInfo) {
  // Override API name
  resources.restApi.addPropertyOverride("Name", {
    "Fn::Join": [
      "",
      [
        "resouremanager",
        "-",
        { "Ref": "env" }
      ]
    ]
  });

  // Add a parameter to your CloudFormation Template for the User Pool's ID
  resources.addCfnParameter(
    {
      type: "String",
      description: "The id of an existing User Pool to connect. If this is changed, a user pool will not be created for you.",
      default: "NONE"
    },
    "AuthCognitoUserPoolId",
    { "Fn::GetAtt": ["authresourcemanager", "Outputs.UserPoolId"] }
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
          { 'Fn::Sub': 'arn:aws:cognito-idp:${AWS::Region}:${AWS::AccountId}:userpool/${AuthCognitoUserPoolId}' }
        ]
      }
    }
  });

  // Remove unwanted endpoints
  if (resources.restApi.body.paths["/vpc/{proxy+}"]) {
    delete resources.restApi.body.paths["/vpc/{proxy+}"];
  }
  if (resources.restApi.body.paths["/vpc/{name}/{proxy+}"]) {
    delete resources.restApi.body.paths["/vpc/{name}/{proxy+}"];
  }

  // --- Convert /vpc ANY method to POST ---
  const vpcPath = resources.restApi.body.paths["/vpc"];
  if (vpcPath && vpcPath["x-amazon-apigateway-any-method"]) {
    const anyMethod = vpcPath["x-amazon-apigateway-any-method"];
    // Create a new POST method by copying properties from the ANY method
    vpcPath["post"] = {
      consumes: anyMethod.consumes,
      produces: anyMethod.produces,
      parameters: anyMethod.parameters,
      responses: anyMethod.responses, // ensure responses are copied
      "x-amazon-apigateway-integration": {
        ...anyMethod["x-amazon-apigateway-integration"],
        httpMethod: "POST"
      },
      security: anyMethod.security
    };
    // Remove the original ANY method
    delete vpcPath["x-amazon-apigateway-any-method"];

    // (Optional) Add or update the Authorization header parameter if needed
    resources.restApi.addPropertyOverride(
      `Body.paths./vpc.post.parameters`,
      [
        ...(vpcPath["post"].parameters || []),
        {
          name: "Authorization",
          in: "header",
          required: false,
          type: "string"
        }
      ]
    );
    // Apply the Cognito security override for the POST method
    resources.restApi.addPropertyOverride(
      `Body.paths./vpc.post.security`,
      [{ Cognito: [] }]
    );
  }

  // --- Convert /vpc/{name} ANY method to GET ---
  const vpcIdPath = resources.restApi.body.paths["/vpc/{name}"];
  if (vpcIdPath && vpcIdPath["x-amazon-apigateway-any-method"]) {
    const anyMethod = vpcIdPath["x-amazon-apigateway-any-method"];
    // Create a new GET method by copying properties from the ANY method
    vpcIdPath["get"] = {
      consumes: anyMethod.consumes,
      produces: anyMethod.produces,
      parameters: anyMethod.parameters,
      responses: anyMethod.responses, // ensure responses are copied
      "x-amazon-apigateway-integration": {
        ...anyMethod["x-amazon-apigateway-integration"],
        httpMethod: "POST"
      },
      security: anyMethod.security
    };
    // Remove the original ANY method
    delete vpcIdPath["x-amazon-apigateway-any-method"];

    // (Optional) Add or update the Authorization header parameter if needed
    resources.restApi.addPropertyOverride(
      `Body.paths./vpc/{name}.get.parameters`,
      [
        ...(vpcIdPath["get"].parameters || []),
        {
          name: "Authorization",
          in: "header",
          required: false,
          type: "string"
        }
      ]
    );
    // Apply the Cognito security override for the GET method
    resources.restApi.addPropertyOverride(
      `Body.paths./vpc/{name}.get.security`,
      [{ Cognito: [] }]
    );
  }
}
