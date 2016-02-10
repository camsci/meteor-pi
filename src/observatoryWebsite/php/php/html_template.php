<?php

// html_template.php
// Meteor Pi, Cambridge Science Centre
// Dominic Ford

require_once "constants.php";
require_once "user.php";

class HTMLtemplate
{
    public static function breadcrumb($items, $area, $postbreadcrumb = null)
    {
        global $const;
        $server = $const->server;
        if (is_null($items)) return;
        if ($area == "home") {
            array_unshift($items, ["index.php", "Home"]);
        } else if ($area == "whattodo") {
            array_unshift($items, ["whattodo.php", "What to do"]);
        } else if ($area == "search") {
            array_unshift($items, ["search.php", "Search the sky"]);
        } else if ($area == "projects") {
            array_unshift($items, ["projects.php", "Projects"]);
        } else if ($area == "howitworks") {
            array_unshift($items, ["howitworks.php", "How it works"]);
        } else if ($area == "cameras") {
            array_unshift($items, ["map.php", "Cameras"]);
        } else if ($area == "faqs") {
            array_unshift($items, ["faqs.php", "FAQs"]);
        } else if ($area == "about") {
            array_unshift($items, ["about.php", "About"]);
        }
        array_unshift($items, ["", "Home"]);
        ?>
        <table style="margin-top:18px;">
            <tr>
                <td class="snugtop" style="white-space:nowrap;">
                    <p class="smtext" style="padding:12px 0 6px 0;">
                        <?php
                        $firstItem = true;
                        foreach ($items as $arg) {
                            print '<span class="chevron_holder">';
                            if (!$firstItem) print '<span class="chevronsep">&nbsp;</span>';
                            print "<a class='chevron' href='{$server}{$arg[0]}'>{$arg[1]}</a></span>";
                            $firstItem = false;
                        }
                        ?>
                    </p></td>
                <?php if ($postbreadcrumb): ?>
                    <td style="padding-left:20px;vertical-align:middle;">
                        <span class="postchevron">
<?php
$first = true;
foreach ($postbreadcrumb as $c) {
    $cname = str_replace(" ", "&nbsp;", htmlentities($c[1], ENT_QUOTES));
    if (!$first) {
        print "&nbsp;| ";
    } else {
        $first = false;
    }
    print "<a href=\"{$server}{$c[0]}\">" . $cname . "</a>";
}
?>
                        </span>
                    </td>
                <?php endif; ?>
            </tr>
        </table>
        <?php
    }

    public static function require_html5()
    {
        ?>
        <!--[if lt IE 9]>
        <p class="smtext" style="background-color:#a00;color:white;border:1px solid #222;margin:16px 4px;padding:8px;">
            <b>
                You appear to be using an old web browser which may not be compatible with the interactive elements of
                this website. This page is compatible with most modern web browsers, including Chrome, Firefox, Safari
                and Internet Explorer 9+, but not with older versions of Internet Explorer.
            </b>
        </p>
        <![endif]-->
        <?php
    }

    public static function header($pageInfo)
    {
        global $const, $user;
        if (!isset($pageInfo["breadcrumb"])) $pageInfo["breadcrumb"] = [];
        if (!isset($pageInfo["postbreadcrumb"])) $pageInfo["postbreadcrumb"] = null;
        $server = $const->server;
        $server_json = $const->server_json;
        print<<<__HTML__
<!DOCTYPE html>
<html lang="en">
__HTML__;
        ?>
        <head>
            <meta charset="utf-8">
            <meta name="description" content="<?php echo $pageInfo["pageDescription"]; ?>"/>
            <meta name="keywords"
                  content="shooting stars, meteors, camera, night sky"/>
            <meta name="generator" content="Dominic Ford"/>
            <meta name="author" content="Dominic Ford"/>
            <link rel="icon" type="image/png" href="/favicon-32x32.png" sizes="32x32">
            <link rel="icon" type="image/png" href="/favicon-194x194.png" sizes="194x194">
            <link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96">
            <link rel="icon" type="image/png" href="/favicon-16x16.png" sizes="16x16">
            <meta name="viewport" content="width=device-width, initial-scale=1">

            <title id="title1">
                <?php echo $pageInfo["pageTitle"]; ?>
            </title>

            <!--[if lt IE 9]>
            <script src="<?php echo $server; ?>vendor/html5shiv/dist/html5shiv.min.js" type="text/javascript"></script>
            <script src="<?php echo $server; ?>vendor/ExplorerCanvas/excanvas.js" type="text/javascript"></script>
            <![endif]-->
            <!-- build:js -->
            <script type="text/javascript"
                    src="//maps.googleapis.com/maps/api/js?key=AIzaSyCuMsPQjaWPZK8c9Sskll0y5Utd0Oq5cxA&amp;sensor=false"></script>
            <!-- endbuild -->


            <script src="<?php echo $server; ?>vendor/jquery/dist/jquery.min.js" type="text/javascript"></script>
            <script src="<?php echo $server; ?>vendor/jquery-ui/jquery-ui.min.js" type="text/javascript"></script>
            <link rel="stylesheet" type="text/css"
                  href="<?php echo $server; ?>vendor/jquery-ui/themes/ui-darkness/jquery-ui.min.css"/>
            <style type="text/css">
                .ui-slider-horizontal .ui-state-default {
                    background: url(<?php echo $server; ?>/images/sliderarrow.png) no-repeat;
                    width: 9px;
                    height: 20px;
                    border: 0 none;
                    margin-left: -4px;
                }

                .ui-slider-vertical .ui-state-default {
                    background: url(<?php echo $server; ?>/images/slidervarrow.png) no-repeat;
                    width: 20px;
                    height: 9px;
                    border: 0 none;
                    margin-left: -4px;
                }
            </style>
            <link rel="stylesheet" href="<?php echo $server; ?>vendor/bootstrap/dist/css/bootstrap.min.css">
            <script src="<?php echo $server; ?>vendor/bootstrap/dist/js/bootstrap.min.js"></script>

            <link rel="stylesheet" type="text/css" href="<?php echo $server; ?>css/style.css" media="all"/>

            <script type="text/javascript" src="<?php echo $server; ?>js/meteorpi.min.js"></script>

            <?php if ($pageInfo["teaserImg"]): ?>
                <link rel="image_src" href="<?php echo $server . $pageInfo["teaserImg"]; ?>"
                      title="<?php echo $pageInfo["pageTitle"]; ?>"/>
                <meta property="og:image" content="<?php echo $server . $pageInfo["teaserImg"]; ?>"/>
            <?php endif; ?>

            <?php echo $pageInfo["cssextra"]; ?>
        </head>

        <?php echo "<body><div class=\"contentwrapper\">"; ?>

        <div class="bannerback">
            <div class="banner">
                <div class="banner_txt_right" id="top">
                    <p class="toptitleA"><a href="#">Meteor Pi</a></p>
                </div>
                <div id="bannerppl"></div>
                <div id="bannercsc"></div>
            </div>
            <div id="bannerfull"></div>
        </div>
        <div class="bannerfade"></div>


        <nav class="navbar navbar-inverse navbar-fixed-top">
            <div class="container-fluid">
                <div class="navbar-header">
                    <a class="navbar-brand" href="<?php echo $server; ?>">Meteor Pi</a>
                </div>
                <div>
                    <ul class="nav navbar-nav">
                        <li class="<?php if ($pageInfo["activeTab"] == "home") echo "active "; ?>">
                            <a href="/">Home</a>
                        </li>
                        <li class="<?php if ($pageInfo["activeTab"] == "whattodo") echo "active "; ?>">
                            <a href="/whattodo.php">What to do</a>
                        </li>
                        <li class="<?php if ($pageInfo["activeTab"] == "search") echo "active "; ?>">
                            <a class="dropdown-toggle" data-toggle="dropdown" href="#">Search the sky<span
                                    class="caret"></span></a>
                            <ul class="dropdown-menu">
                                <li><a href="<?php echo $server; ?>search_moving.php">Moving objects</a></li>
                                <li><a href="<?php echo $server; ?>search_still.php">Still photography</a></li>
                            </ul>
                        </li>
                        <li class="<?php if ($pageInfo["activeTab"] == "projects") echo "active "; ?>">
                            <a href="/projects.php">Projects</a>
                        </li>
                        <li class="<?php if ($pageInfo["activeTab"] == "howitworks") echo "active "; ?>">
                            <a href="/howitworks.php">How it works</a>
                        </li>
                        <li class="dropdown <?php if ($pageInfo["activeTab"] == "cameras") echo "active "; ?>">
                            <a class="dropdown-toggle" data-toggle="dropdown" href="#">Cameras<span
                                    class="caret"></span></a>
                            <ul class="dropdown-menu">
                                <li><a href="<?php echo $server; ?>map.php">Locations</a></li>
                                <li><a href="<?php echo $server; ?>observatory_activity.php">Activity tracker</a></li>
                                <li><a href="<?php echo $server; ?>observatory_metadata.php">Status information</a></li>
                            </ul>
                        </li>
                        <li class="<?php if ($pageInfo["activeTab"] == "faqs") echo "active "; ?>">
                            <a href="/faqs.php">FAQs</a>
                        </li>
                        <li class="<?php if ($pageInfo["activeTab"] == "about") echo "active "; ?>">
                            <a href="/about.php">About</a>
                        </li>
                    </ul>
                    <ul class="nav navbar-nav navbar-right">
                        <li class="<?php if ($pageInfo["activeTab"] == "login") echo "active "; ?>">
                            <a href="/user/login.php">
                                <?php if (is_null($user->username)): ?>
                                    <span class="glyphicon glyphicon-log-in"></span>&nbsp;Log in
                                    <?php else: ?>
                                    <span class="glyphicon glyphicon-user"></span>&nbsp;Your account
                                <?php endif; ?>
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <div class="bannerfade"></div>

        <?php
        print "<div class='container mainpage'>";
        HTMLtemplate::breadcrumb($pageInfo["breadcrumb"], $pageInfo["activeTab"], $pageInfo["postbreadcrumb"]);
        ?>

        <h2><?php echo $pageInfo["pageTitle"]; ?></h2>

        <?php
    }

    public function footer($pageInfo)
    {
        echo "</div>";  // mainpage

        ?>
        <div class="footer">
            <div class="container">
                <div class="row">
                    <div class="col-sm-2" style="text-align:center;padding:4px;">
                    </div>

                    <div class="col-sm-4" style="padding:4px;">
                        <p class="copyright">
                            <span style="font-size:15px;">
                            &copy; <a href="#about">Cambridge Science Centre 2016.</a>
                            </span>
                        </p>

                        <p class="copyright">
                            For more information about Meteor Pi, <a href="#about">click here</a>.<br/>
                            Website designed by Dominic Ford.<br/>
                        </p>

                        <p class="copyright">
                            Top banner image courtesy of Markus Lubjuhn.
                        </p>
                    </div>
                    <div class="col-sm-6" style="padding:4px;">
                        <p class="copyright">Contact us via</p>

                        <div style="display:inline-block;text-align:center;padding:3px 10px;">
                            <a href="https://www.facebook.com/meteorpicamera/">
                                <div class="mp-img mp-img-fb"></div>
                                <br/>Facebook</a>
                        </div>
                        <div style="display:inline-block;text-align:center;padding:3px 10px;">
                            <a href="https://twitter.com/meteorpi">
                                <div class="mp-img mp-img-tweet"></div>
                                <br/>Twitter</a>
                        </div>

                    </div>
                </div>
            </div>
        </div>

        <?php
        print "</body></html>";
    }

    static public function listObstories($obstories, $urlstub)
    {
        ?>
        <h4 style="padding:20px 0;">Our cameras</h4>

        <?php foreach ($obstories as $obstory): ?>
        <p class="select-list">
            <a href="<?php echo $urlstub . $obstory['publicId']; ?>">
                <?php echo $obstory['name']; ?>
            </a>
        </p>
    <?php endforeach; ?>
        <?php
    }

    static public function imageGallery($result_list, $url_stub)
    {
        global $const;
        ?>
        <div class="row">
            <?php foreach ($result_list as $item): ?>
                <div class="col-md-3 gallery_item">
                    <a href="<?php echo $url_stub . $item['linkId']; ?>">
                        <div class="gallery_image">
                            <?php if ($item['mimeType'] == 'image/png'): ?>
                                <img class="gallery_img" alt="" title="" src="/api/thumbnail/<?php
                                echo $item['fileId'] . "/" . $item['filename'];
                                ?>"/>
                            <?php elseif (array_key_exists($item['mimeType'], $const->mimeTypes)): ?>
                                <div class="image_substitute gallery_img">
                                    <div class="mimetype">
                                        <?php echo $const->mimeTypes[$item['mimeType']]; ?>
                                    </div>
                                </div>
                            <?php else: ?>
                                <div class="image_substitute">
                                    <div class="mimetype">FILE</div>
                                </div>
                            <?php endif; ?>
                        </div>
                        <div class="gallery_text">
                            <?php echo $item['caption'] ?>
                        </div>
                    </a>
                    <div class="gallery_extra">
                        <?php echo $item['hover']; ?>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
        <?php
    }

    static public function showPager($result_count, $pageNum, $pageSize, $self_url)
    {
        $Npages = floor($result_count / $pageSize);
        $pageMin = max($pageNum - 5, 1);
        $pageMax = min($pageMin + 9, $Npages + 1);

        print "<div class='pager'>Page ";
        for ($p = $pageMin; $p <= $pageMax; $p++) {
            print "<span class='page'>";
            if ($p != $pageNum) print "<a href='{$self_url}&page={$p}'>";
            else print "<b>";
            print $p;
            if ($p != $pageNum) print "</a>";
            else print "</b>";
            print "</span>";
        }
        print "</div>";
    }
}

$pageTemplate = new HTMLtemplate();
