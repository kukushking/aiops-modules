# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys

import aws_cdk as cdk
import cdk_nag
import pytest
from aws_cdk.assertions import Annotations, Match, Template


@pytest.fixture(scope="function")
def stack_defaults() -> None:
    os.environ["CDK_DEFAULT_ACCOUNT"] = "111111111111"
    os.environ["CDK_DEFAULT_REGION"] = "us-east-1"

    # Unload the app import so that subsequent tests don't reuse
    if "stack" in sys.modules:
        del sys.modules["stack"]


@pytest.fixture(scope="function")
def stack(
    stack_defaults,
    enable_custom_sagemaker_projects: bool,
    auth_mode: str,
    mlflow_enabled: bool,
    enable_jupyterlab_app: bool,
) -> cdk.Stack:
    import stack

    app = cdk.App()
    project_name = "test-project"
    dep_name = "test-deployment"
    mod_name = "test-module"
    studio_domain_name = "test-domain"
    studio_bucket_name = "test-bucket"
    data_science_users = ["ds-user-1"]
    lead_data_science_users = ["lead-ds-user-1"]
    app_image_config_name = None
    image_name = None
    mlflow_server_name = "mlflow"
    mlflow_server_version = None
    mlflow_server_size = None
    mlflow_artifact_store_bucket_name = "bucket"
    mlflow_artifact_store_bucket_prefix = "/"
    enable_jupyterlab_app_sharing = False
    jupyterlab_app_instance_type = None

    return stack.SagemakerStudioStack(
        app,
        f"{project_name}-{dep_name}-{mod_name}",
        vpc_id="vpc-12345",
        subnet_ids=["subnet-12345", "subnet-54321"],
        studio_domain_name=studio_domain_name,
        studio_bucket_name=studio_bucket_name,
        data_science_users=data_science_users,
        lead_data_science_users=lead_data_science_users,
        app_image_config_name=app_image_config_name,
        image_name=image_name,
        enable_custom_sagemaker_projects=enable_custom_sagemaker_projects,
        enable_jupyterlab_app=enable_jupyterlab_app,
        enable_jupyterlab_app_sharing=enable_jupyterlab_app_sharing,
        jupyterlab_app_instance_type=jupyterlab_app_instance_type,
        auth_mode=auth_mode,
        mlflow_enabled=mlflow_enabled,
        mlflow_server_name=mlflow_server_name,
        mlflow_server_version=mlflow_server_version,
        mlflow_server_size=mlflow_server_size,
        mlflow_artifact_store_bucket_name=mlflow_artifact_store_bucket_name,
        mlflow_artifact_store_bucket_prefix=mlflow_artifact_store_bucket_prefix,
        env=cdk.Environment(
            account=os.environ["CDK_DEFAULT_ACCOUNT"],
            region=os.environ["CDK_DEFAULT_REGION"],
        ),
        enable_domain_resource_isolation=True,
    )


@pytest.mark.parametrize("auth_mode", ["IAM", "SSO"])
@pytest.mark.parametrize("mlflow_enabled", [True, False])
@pytest.mark.parametrize("enable_custom_sagemaker_projects", [True, False])
@pytest.mark.parametrize("enable_jupyterlab_app", [True, False])
def test_synthesize_stack(
    stack: cdk.Stack,
    enable_custom_sagemaker_projects: bool,
    auth_mode: str,
    mlflow_enabled: bool,
    enable_jupyterlab_app: bool,
) -> None:
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::SageMaker::Domain", 1)
    template.resource_count_is("AWS::SageMaker::UserProfile", 2)
    template.resource_count_is("AWS::EC2::SecurityGroup", 1)
    template.resource_count_is("AWS::IAM::Role", 6 if enable_custom_sagemaker_projects else 4)
    template.resource_count_is("AWS::SageMaker::MlflowTrackingServer", 1 if mlflow_enabled else 0)
    template.resource_count_is("AWS::SageMaker::Space", 2 if enable_jupyterlab_app else 0)


@pytest.mark.parametrize("auth_mode", ["IAM", "SSO"])
@pytest.mark.parametrize("mlflow_enabled", [True, False])
@pytest.mark.parametrize("enable_custom_sagemaker_projects", [True, False])
@pytest.mark.parametrize("enable_jupyterlab_app", [True, False])
def test_no_cdk_nag_errors(
    stack: cdk.Stack,
    enable_custom_sagemaker_projects: bool,
    auth_mode: str,
    mlflow_enabled: bool,
    enable_jupyterlab_app: bool,
) -> None:
    cdk.Aspects.of(stack).add(cdk_nag.AwsSolutionsChecks())

    nag_errors = Annotations.from_stack(stack).find_error(
        "*",
        Match.string_like_regexp(r"AwsSolutions-.*"),
    )
    assert not nag_errors, f"Found {len(nag_errors)} CDK nag errors"
