"""
Created on 2022-04-07

@author: wf
"""

import mwdocker


class Version(object):
    """
    Version handling for pymediawikidocker
    """

    name = "pymediawikidocker"
    version = mwdocker.__version__
    date = "2021-06-21"
    updated = "2025-11-14"

    authors = "Wolfgang Fahl, Tim Holzheim"

    description = (
        "Python controlled (semantic) mediawiki docker application cluster installation"
    )

    cm_url = "https://github.com/WolfgangFahl/pymediawikidocker"
    chat_url = "https://github.com/WolfgangFahl/pymediawikidocker/discussions"
    doc_url = "https://wiki.bitplan.com/index.php/Pymediawikidocker"

    license = f"""Copyright 2020-2025 contributors. All rights reserved.
  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied."""
    longDescription = f"""{name} version {version}
{description}
  Created by {authors} on {date} last updated {updated}"""
