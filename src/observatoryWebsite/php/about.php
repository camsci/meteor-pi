<?php

// about.php
// Meteor Pi, Cambridge Science Centre
// Dominic Ford

require "php/imports.php";

$pageInfo = [
    "pageTitle" => "About Meteor Pi",
    "pageDescription" => "Meteor Pi",
    "activeTab" => "about",
    "teaserImg" => null,
    "cssextra" => null,
    "includes" => [],
    "linkRSS" => null,
    "options" => []
];

$pageTemplate->header($pageInfo);

?>

<div class="rightimg">
    <img src="/img/IMG_20150910_193401.jpg" /><br />
    <b>Three Meteor Pi cameras being tested side-by-side.</b>
</div>

<p class="text">Meteor Pi was developed by Cambridge Science Centre as part of its 2015-16 Cosmic Exhibition. The hardware designs and software used by the
    Meteor Pi cameras is all open source, and can be found on our <a href="https://github.com/camsci/meteor-pi">GitHub pages</a>.
</p>

<h3>The Meteor Pi Team</h3>

<table class="developers">
    <tr>
        <td>Lead Developer</td>
        <td>Dominic Ford</td>
    </tr>
    <tr>
        <td>Data Transport</td>
        <td>Tom Oinn</td>
    </tr>
    <tr>
        <td>Hardware Design</td>
        <td>Dave Ansell</td>
    </tr>
</table>

<p class="text">
    If you'd like to get involved, why not try building your own Meteor Pi camera?
    For more information, visit our <a href="https://github.com/camsci/meteor-pi">GitHub pages</a>.
</p>

<h3>Supporters</h3>

<p>The development of Meteor Pi was made possible thanks to generous support from:</p>

<div class="row supporters">
    <div class="col-sm-6">
        <img src="img/rpi_logo.png" alt="The Raspberry Pi Foundation"
             title="The Raspberry Pi Foundation"/>
        <br />
        The Raspberry Pi Foundation
    </div>
    <div class="col-sm-6">
        <img src="img/Mathworks.jpg" alt="MathWorks" title="MathWorks"/>
        <br />
        MathWorks
    </div>
</div>

<?php
$pageTemplate->footer($pageInfo);
