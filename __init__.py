# -*- coding: utf-8 -*-

"""
***************************************************************************
* Plugin Name: Map-X
* Version    : 1.0.2
* Author     : Jujun Junaedi
* Email      : jujun.junaedi@outlook.com
* Description: Advanced multi-view analysis tool (2, 3, 4 views) with live sync, smart Z-ordering, and real-time statistical legend.
* License    : GPL-2.0-or-later
* Motto      : "Sebaik-baiknya Manusia adalah yang bermanfaat bagi sesama"
***************************************************************************
"""

def classFactory(iface):
    """
    Load the MultiViewPlugin class from the multiview module.
    
    :param iface: A reference to the QGIS desktop interface.
    :type iface: qgis.gui.QgisInterface
    """
    # Mengambil class MapXPlugin dari mapx.py
    from .mapx import MapXPlugin
    return MapXPlugin(iface)