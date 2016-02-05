<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.8.1-Wien" minimumScale="-4.65661e-10" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="0" classificationMax="60" classificationMinMaxOrigin="CumulativeCutFullExtentEstimated" band="27" classificationMin="0" type="singlebandpseudocolor">
      <rasterTransparency/>
      <rastershader>
        <colorrampshader colorRampType="EXACT" clip="0">
          <item alpha="255" value="0" label="No Agent" color="#bbb9b2"/>
          <item alpha="255" value="1" label="Clearcut" color="#543005"/>
          <item alpha="255" value="2" label="Partial Harvest" color="#3b87bd"/>
          <item alpha="255" value="3" label="Development" color="#cab2d6"/>
          <item alpha="255" value="4" label="Fire" color="#d33502"/>
          <item alpha="255" value="6" label="Insects/Long Disturbance" color="#ef6a32"/>
          <item alpha="255" value="30" label="Long Slow Disturbance" color="#fbbf45"/>
          <item alpha="255" value="35" label="Fast Disturbance" color="#710162"/>
          <item alpha="255" value="50" label="Growth" color="#017354"/>
          <item alpha="255" value="60" label="Non-forests" color="#000000"/>
          <item alpha="0" value="70" label="No Data" color="#ff00ff"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="31" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
