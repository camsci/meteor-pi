
var graphjs = new Object;

// Utility functions
graphjs.frange = function(min,max,step)
 {
  var output = [];
  for (var x=min; x<max; x+=step) output.push(x);
  return output;
 }

graphjs.getexponent = function(x, logBase)
 {
  return math.floor(math.log(x)/Math.log(logBase));
 }

graphjs.getmantissa = function(x, logBase)
 {
  var exponent = math.floor(math.log(x)/Math.log(logBase));
  return x/math.pow(logBase,exponent);
 }

graphjs.factorise = function(x)
 {
  factors = [];
  for (var i=0; i<x/2+1; i++) if (x%i == 0) factors.push(i);
  return factors;
 }

// Graph class
graphjs.graph = function(holder, canvas, datasets, settings, xsettings, ysettings)
 {
  this.holder = holder;
  this.canvas = canvas;
  this.datasets = datasets;
  this.xsettings = xsettings;
  this.ysettings = ysettings;
  this.settings = {'aspectRatio': 0.5,
                   'axisCol': '#222',
                   'axisWidth': 1,
                   'gridShow': 1,
                   'gridCol': ["#c0c0c0","#e0e0e0"],
                   'gridWidth': [1,1],
                   'margins': [20,20,60,60],
                   'tickCol': '#222',
                   'tickLength': [12,6],
                   'tickTextCol': '#222',
                   'tickFont': '14px Arial,Helvetica,sans-serif',
                   'tickWidth': 1,
                  };
  jQuery.extend(this.settings,settings);

  // Draw graph
  this.draw = function()
   {
    var canvas = document.getElementById(this.canvas);
    var c = canvas.getContext('2d');
    var w = this.width;
    var h = this.height;
    var m = this.settings['margins'];

    // Clear canvas
    canvas.width = w;
    canvas.height = h;

    // Plot region has margin around it
    var x0 = m[3];
    var x1 = w - m[1] - m[3];
    var y0 = m[0];
    var y1 = h - m[0] - m[2];

    // Assign axes
    var xdata = this.datasets.map( function(a) { return a['xdata']; } ).reduce( function(a,b) { return a.concat(b); } );
    var ydata = this.datasets.map( function(a) { return a['ydata']; } ).reduce( function(a,b) { return a.concat(b); } );
    this.xaxis = new graphjs.axis(x0 , x1 , xdata , this.xsettings);
    this.yaxis = new graphjs.axis(y0 , y1 , ydata , this.ysettings);

    // Draw grid
    if (this.settings['gridShow'])
     for (var gridLevel=0; gridLevel<2; gridLevel++)
      {
       c.strokeStyle=this.settings['gridCol'][gridLevel];
       c.lineWidth=this.settings['gridWidth'][gridLevel];

       // Vertical lines
       for (var i=0; i<this.xaxis.ticks[gridLevel].length; i++)
        {
         var x = this.xaxis.project(this.xaxis.ticks[gridLevel][i]);
         c.beginPath(); c.moveTo(x,y0); c.lineTo(x,y1); c.stroke();
        }

       // Horizontal lines
       for (var i=0; i<this.yaxis.ticks[gridLevel].length; i++)
        {
         var y = this.yaxis.project(this.yaxis.ticks[gridLevel][i]);
         c.beginPath(); c.moveTo(x0,y); c.lineTo(x1,y); c.stroke();
        }
      }

    // Draw ticks
    c.strokeStyle=this.settings['tickCol'];
    c.lineWidth=this.settings['tickWidth'];

    for (var gridLevel=0; gridLevel<2; gridLevel++)
     {
      for (var i=0; i<this.xaxis.ticks[gridLevel].length; i++)
       {
        var x = this.xaxis.project(this.xaxis.ticks[gridLevel][i]);
        c.beginPath(); c.moveTo(x,y0); c.lineTo(x,y0+this.settings['tickLength'][gridLevel]); c.stroke();
        c.beginPath(); c.moveTo(x,y1); c.lineTo(x,y1-this.settings['tickLength'][gridLevel]); c.stroke();
       }

      for (var i=0; i<this.yaxis.ticks[gridLevel].length; i++)
       {
        var y = this.yaxis.project(this.yaxis.ticks[gridLevel][i]);
        c.beginPath(); c.moveTo(x0,y); c.lineTo(x0+this.settings['tickLength'][gridLevel],y); c.stroke();
        c.beginPath(); c.moveTo(x1,y); c.lineTo(x1-this.settings['tickLength'][gridLevel],y); c.stroke();
       }
     }

    // Label ticks
    c.fillStyle=this.settings['tickTextCol'];
    c.font=this.settings['tickFont'];

    c.textBaseline = 'top';
    c.textAlign = 'center';
    for (var i=0; i<this.xaxis.ticks[0].length; i++)
     {
      var x = this.xaxis.project(this.xaxis.ticks[0][i]);
      c.fillText(this.xaxis.tickText(this.xaxis.ticks[0][i]) , x , y1+8);
     }

    c.textBaseline = 'middle';
    c.textAlign = 'right';
    for (var i=0; i<this.yaxis.ticks[0].length; i++)
     {
      var y = this.yaxis.project(this.yaxis.ticks[0][i]);
      c.fillText(this.yaxis.tickText(this.yaxis.ticks[0][i]) , x0-8 , y);
     }

    // Plot datasets
    for (var i=0; i<this.datasets.length; i++)
     {
      var d = this.datasets[i];
      var settings = {'color': '#ff0000', 'linewidth':2};
      jQuery.extend(settings,d['settings']);
      c.strokeStyle=settings['color'];
      c.lineWidth=settings['linewidth'];
      c.beginPath();
      c.moveTo( this.xaxis.project(d['xdata'][0]) , this.yaxis.project(d['ydata'][0]) );
      for (var j=0; j<d['xdata'].length; j++) c.lineTo( this.xaxis.project(d['xdata'][j]) , this.yaxis.project(d['ydata'][j]) );
      c.stroke();
     }

    // Draw edge of plot
    c.strokeStyle=this.settings['axisCol'];
    c.lineWidth=this.settings['axisWidth'];
    c.rect(x0,y0,x1-x0,y1-y0); c.stroke();
   }

  // Make graph canvas reponsive to size of holder
  this.resizeCanvas = function()
   {
    var width  = $("#"+this.holder).width();
    var height = $("#"+this.holder).height();
    var aspect = this.settings['aspectRatio'];
    var canvas = $("#"+this.canvas);
    this.width = width;
    this.height= aspect ? (width*aspect) : height;
    this.draw();
   }
  var this_=this; // Because Javascript is awesomely elegant...
  window.addEventListener('resize', function(){this_.resizeCanvas();}, false);
  this.resizeCanvas();
 }

// Axis class
graphjs.axis = function(x0, x1, datasets, settings)
   {
    this.x0 = x0;
    this.x1 = x1;
    this.datasets = datasets;
    this.settings = {'log': 0,
                     'logBase': 10,
                     'factorMultiply': 2, // Factorise logBase**2, so that 0.00,0.25,0.50,0.75,1.00 is a valid factorisation
                     'ticksMax': 100,
                     'ticksMin': 2,
                     'ticksTargetSep': [ 80 , 30 ]
                    };
    jQuery.extend(this.settings,settings);

    this.setAutoRange = function()
     {
      // Automatically scale out range of axis to start and end on a round number

      var logBase = this.settings['logBase'];
      // Work out order of magnitude of range of axis
      var OoM = Math.pow(logBase, Math.floor(Math.log(this.datamax - this.datamin) / Math.log(logBase)));

      // Round the limits of the axis outwards to nearest round number
      this.axismin = Math.floor(this.datamin / OoM) * OoM;
      this.axismax = Math.ceil (this.datamax / OoM) * OoM;
     }

    this.generateLogTickSchemes = function()
     {
      var logBase = this.settings['logBase'];
      var stopping, divisor;
      var tickSchemes = [];

      for (stopping=0,divisor=1; (!stopping); divisor++)
       {
        var tickScheme = {'mantissas':[]};
        for (var i=0; i<divisor; i++)
         {
          tickScheme['mantissa'].push( Math.round(Math.pow(logBase,i/divisor)));
          if ((i>0)&&(tickScheme['mantissa'][i-1]==tickScheme['mantissa'][i])) stopping=1;
         }
        if (!stopping)
         {
          tickScheme['ticksep'] = 1.0;
          tickScheme['offset']  = 0.0;
          tickSchemes.push(tickScheme);
         }
       }
      var tickScheme = {'mantissas':[]};
      for (i=1; i<LogBase; i++) tickScheme['mantissas'].push(i);
      tickScheme['ticksep'] = 1.0;
      tickScheme['offset']  = 0.0;
      tickSchemes.push(tickScheme);
      return;
     }

    this.generateTickSchemes = function(OoM, isLog, factorsLogBase)
     {
      var logBase = this.settings['logBase'];
      var i, levelDescend = 1;
      var tickSchemes = [];
      while (Math.pow(logBase,levelDescend-1) < (10.0 * this.settings['ticksMax']))
       {
        var OoMscan = OoM / Math.pow(logBase, levelDescend);
        if (isLog && (OoMscan==1/logBase))
         {
          tickSchemes = tickSchemes.concat( this.generateLogTickSchemes() );
         }
        else
         {
          for (var i=factorsLogBase.length-1; i>=0; i--)
           {
            var t = factorsLogBase[i] / Math.pow(logBase, this.settings['factorMultiply']-1);
            if ((!isLog) || (t==Math.round(t))) // Fractional steps (i.e. sqrts) not allowed
             {
              var tickScheme = {};
              tickScheme['mantissas'] = [1];
              tickScheme['ticksep']   = t * OoMscan;
              tickScheme['offset']    = 0.0;
              tickSchemes.push(tickScheme);
             }
           }
         }
        levelDescend++;
       }
      return tickSchemes;
     }

    this.setAxisTicks = function()
     {
      var logBase = this.settings['logBase'];
      var factorsLogBase = graphjs.factorise( Math.pow(logBase,this.settings['factorMultiply']) );
      var isLog = this.settings['log'];

      var OoM, axis_min, axis_max, axis_min_l, axis_max_l, outer_min, outer_max;

      // Work out order of magnitude of axis range
      axis_min = this.axismin;
      axis_max = this.axismax;
      if      (axis_min  > axis_max) { var swap = axis_min; axis_min = axis_max; axis_max = swap; }
      else if (axis_min == axis_max) { axis_max+=1; }
      if (isLog && (axis_max < 3*axis_min)) isLog = 0;
      if (!isLog)
       {
        OoM       = Math.pow(10.0, Math.ceil(Math.log(axis_max - axis_min)/Math.log(10)));
        outer_min = Math.floor(axis_min / OoM) * OoM;
        outer_max = Math.ceil (axis_max / OoM) * OoM;
       }
      else
       {
        axis_min_l = Math.log(axis_min) / Math.log(LogBase);
        axis_max_l = Math.log(axis_max) / Math.log(LogBase);
        OoM        = Math.pow(10.0, Math.ceil(Math.log(axis_max_l - axis_min_l)/Math.log(10)));
        outer_min  = Math.floor(axis_min_l / OoM) * OoM;
        outer_max  = Math.ceil (axis_max_l / OoM) * OoM;
       }

      // Deal with MAJOR ticks. Then MINOR ticks.
      this.ticks = [ [] , [] ];
      for (var major=1; major>=0; major--)
       {
         var tickLevel = 1-major;
         // How many ticks can we fit onto this axis?
         var number_ticks = Math.floor((x1-x0) / this.settings['ticksTargetSep'][tickLevel]) + 1;
         if (number_ticks > this.settings['ticksMax']) number_ticks = this.settings['ticksMax']; // Maximum number of ticks along any given axis
         if (number_ticks < this.settings['ticksMin']) number_ticks = this.settings['ticksMin']; // Minimum of two ticks along any given axis

         // Generate list of potential tick schemes
         tickSchemes = this.generateTickSchemes(OoM, isLog, factorsLogBase);
         tickListBest = [];

         // Try each tick scheme in turn
         for (var n=0; n<tickSchemes.length; n++)
          {
           var t = tickSchemes[n];
           var ts_min = outer_min  + t['offset'];
           var tickListTrial = [];
           for (var j=0; j<1.5+(outer_max-outer_min)/t['ticksep']; j++)
            {
             for (var k=0; k<t['mantissas'].length; k++)
              {
               var x = ts_min + j * t['ticksep'];
               if (Math.abs(x)<1e-6*t['ticksep']) x=0;
               if (isLog) x = Math.pow(logBase, x);
               x *= t['mantissas'][k];
               if ((x<axis_min) || (x>axis_max)) continue;
               tickListTrial.push(x);
              }
            }

           // Make sure that this set of ticks overlays ticks_overlay
           var matched = true;
           if (!major)
            {
             var majorTicks = this.ticks[0];
             var minorTicks = tickListTrial;
             for (var i=0; i<majorTicks.length; i++)
              {
               matched = false;
               for (var k=0; k<minorTicks.length; k++)
                {
                 if ( Math.abs(this.project(minorTicks[k]) - this.project(majorTicks[i]))<1 ) // Because of the vaguaries of float arithmetic, values may not test equal. But are they within 1 pixel??
                  {
                   matched = true;
                   break;
                  }
                }
               if (!matched) break;
              }
             if (!matched) continue;
            }

           // See whether this tick scheme is better than previous
           if ((isLog)&&(t['mantissas'].length>=logBase-1)&&(!major))
            {
             if (tickListTrial.length > 3*number_ticks) break;
             tickListBest = tickListTrial;
            }
           else if ((isLog)&&(t['mantissas'].length>1)&&(tickListTrial.length>number_ticks))
            {
             continue;
            }
           else if (tickListTrial.length > number_ticks) break;
           else if (tickListTrial.length > tickListBest.length )
            {
             tickListBest = tickListTrial;
            }
          }

         // Commit list of ticks
         this.ticks[tickLevel] = tickListBest;
       }
     }

    this.tickText = function(x)
     {
      return x.toString();
     }

    // Convert axis value into a pixel position
    this.project = function(x)
     {
      var p;
      if (this.settings['log']) { p = Math.log( x/this.axismin ) / Math.log( this.axismax/this.axismin ); }
      else                      { p = (x-this.axismin) / (this.axismax-this.axismin); }
      return x0 + (x1-x0) * p;
     }

    // Constructor

    // Determine spread of data
    this.datamin = Math.min.apply(Math, this.datasets);
    this.datamax = Math.max.apply(Math, this.datasets);
    this.setAutoRange();
    this.setAxisTicks();
   }
