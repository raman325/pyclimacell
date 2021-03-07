====================
Python ClimaCell API
====================


.. image:: https://img.shields.io/pypi/v/pyclimacell.svg
        :target: https://pypi.python.org/pypi/pyclimacell

.. image:: https://img.shields.io/travis/raman325/pyclimacell.svg
        :target: https://travis-ci.com/raman325/pyclimacell

.. image:: https://readthedocs.org/projects/pyclimacell/badge/?version=latest
        :target: https://pyclimacell.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



Python3.7+ package to access the `ClimaCell Weather API <https://www.climacell.co/weather-api/>`_

Both an async module (``ClimaCellV4`` and ``ClimaCellV3``) and a synchronous module
(``ClimaCellV3Sync`` and ``ClimaCellV4Sync``) are provided.

Example Code
-------------
.. code-block:: python

  from pyclimacell import ClimaCellV4Sync
  api = ClimaCellSync("MY_API_KEY", latitude, longitude)
  print(api.realtime(api.available_fields(timedelta(0))))
  print(api.forecast_nowcast(api.available_fields(timedelta(minutes=5))), start_time, timedelta_duration, timestep))

Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
