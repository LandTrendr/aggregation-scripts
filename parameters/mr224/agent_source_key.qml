<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.8.1-Wien" minimumScale="0" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="-1" classificationMax="60" classificationMinMaxOrigin="CumulativeCutFullExtentEstimated" band="3" classificationMin="0" type="singlebandpseudocolor">
      <rasterTransparency/>
      <rastershader>
        <colorrampshader colorRampType="EXACT" clip="0">
          <item alpha="255" value="0" label="No Agent" color="#ffdddd"/>
          <item alpha="255" value="1" label="Clearcut" color="#4444cc"/>
          <item alpha="255" value="2" label="Partial Harvest" color="#5588ff"/>
          <item alpha="255" value="3" label="Development" color="#ffff22"/>
          <item alpha="255" value="4" label="Fire" color="#ee0000"/>
          <item alpha="255" value="6" label="Insect/Disease" color="#ff9955"/>
          <item alpha="255" value="7" label="Road" color="#000000"/>
          <item alpha="255" value="9" label="False Change" color="#dddddd"/>
          <item alpha="255" value="10" label="Unknown Agent" color="#dddddd"/>
          <item alpha="255" value="11" label="Water" color="#0300a3"/>
          <item alpha="255" value="15" label="Debris Flow" color="#883322"/>
          <item alpha="255" value="17" label="Other" color="#dddddd"/>
          <item alpha="255" value="21" label="MPB-29" color="#ff9955"/>
          <item alpha="255" value="22" label="MPB-239" color="#ff9955"/>
          <item alpha="255" value="25" label="WSB-29" color="#ff9955"/>
          <item alpha="255" value="26" label="WSB-239" color="#ff9955"/>
          <item alpha="255" value="30" label="Longest Disturbance" color="#ff9955"/>
          <item alpha="255" value="40" label="Greatest Disturbance" color="#6666dd"/>
          <item alpha="255" value="41" label="Second Greatest Disturbance" color="#6666dd"/>
          <item alpha="255" value="42" label="Other Disturbance" color="#6666dd"/>
          <item alpha="255" value="51" label="Growth" color="#33cc33"/>
          <item alpha="255" value="52" label="Other Growth" color="#33cc33"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="48" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
