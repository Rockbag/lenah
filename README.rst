=====
Lenah
=====


.. image:: https://img.shields.io/pypi/v/lenah.svg
        :target: https://pypi.python.org/pypi/lenah

.. image:: https://img.shields.io/travis/Rockbag/lenah.svg
        :target: https://travis-ci.com/Rockbag/lenah

.. image:: https://readthedocs.org/projects/lenah/badge/?version=latest
        :target: https://lenah.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




Lenah is an opinionated but flexible REST framework for Chalice. It provides a simple interface to define cloud-native CRUD-based endpoints.

Important
_________

This package is currently in **experimental phase**. It is **not** recommended to use this in production currently.


* Free software: MIT license
* Documentation: https://lenah.readthedocs.io.


Features
--------

Restful resource definition:
::

    from chalice import Chalice

    from lenah.resource import RestfulResource, RestfulModelConfiguration
    from lenah.models.pynamodb import PynamoDbModelRepository

    app = Chalice(app_name='endog')

    RestfulResource(app,
                    config=RestfulModelConfiguration(
                        resource_name="posts",
                        input_model=BlogRequest,
                        output_model=BlogResponse,
                        db_model_repository=PynamoDbModelRepository(db_model=BlogPost)
                    )
    )


The definition above will generate the following endpoints:

- GET /v1/posts to list blog posts
- GET /v1/posts/{id} to fetch a specific blog post
- POST /v1/posts to create a new blog post
- PUT /v1/posts/{id} to full update an existing blog post
- PATCH /v1/posts/{id} to json merge patch an existing blog post
- DELETE /v1/posts/{id} to delete an existing blog post
- GET /v1/posts/swagger.json to get the swagger specification for this API (still in development)

The ``list`` endpoint accepts ``pagination_item_count`` and ``pagination_page`` params for pagination.

``input_model`` is a pydantic model that specifies what the request must look like for creating/updating/patching a document. For any invalid request object a ``lenah.responses.BadRequest`` is returned.

``output_model`` is a pydantic model that specifies what the ``data`` block in the response will look like.

``db_model_repository`` defines the type of database used in the backend. Currently only ``PynamoDbModelRepository``,
which is a DynamoDB backend using the PynamoDb library.
Custom db repositories can be added by extending the ``lenah.models.base.ModelRepository`` class.

Other attributes
################

Authorizers
***********

An authorizer can be specified through the ``authorizer`` attribute. This accepts any built-in ``Chalice`` authorizer and applies
it to all the generated endpoints.

Custom, per endpoint authorizers can be written by extending the ``lenah.authorizers.RequestAuthorizer`` class. The authorizer class
must implement the ``check`` method. The ``check`` method arguments depend on the endpoint in question:

- LIST: request(ChaliceRequest), pagination_item_count(int), pagination_page(str)
- GET: request(ChaliceRequest), id
- UPDATE: request(ChaliceRequest), id, input_model(RequestModel)
- PATCH: request(ChaliceRequest), id
- DELETE: request(ChaliceRequest), id
- CREATE: request(ChaliceRequest), input_model(RequestModel)

For example:
::

    from lenah.authorizers import RequestAuthorizer, AuthorizationResult

    class IsOddId(RequestAuthorizer):
        def check(self, request, id):
            is_odd = id % 2 == 1
            message = 'id is not odd' if not is_odd
            return AuthorizationResult(success=is_odd, message=message)

The above authorizer then can be configured on the RestfulResource through the ``extra_authorizers`` attribute.

Like so
::

    RestfulResource(config=RestfulModelConfiguration(extra_authorizers={RestfulActions.GET, [IsOddId()], ...))

If the authorizer evaluates to ``success==False`` a ``lenah.responses.Unauthorized`` response is returned.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
