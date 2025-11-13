(function() {
    var monthIndex = 10;
    var day = 26;
    var hour = 7;
    var minute = 0;

    function onSameDayAfterTarget(now) {
      
      document.getElementById("demo").textContent = "It's past 7:00 AM on November 26 — custom handler not implemented.";
    }

    var now = new Date();
    var year = now.getFullYear();

    var target = new Date(year, monthIndex, day, hour, minute, 0, 0);

    if (now.getMonth() === monthIndex && now.getDate() === day && now.getTime() > target.getTime()) {
      onSameDayAfterTarget(now);
      return;
    }

    if (now >= target) {
      target = new Date(year + 1, monthIndex, day, hour, minute, 0, 0);
    }

    var countDownDate = target.getTime();

    var x = setInterval(function() {
      var now = new Date().getTime();
      var distance = countDownDate - now;

      if (distance <= 0) {
        clearInterval(x);
        document.getElementById("demo").textContent = "EXPIRED";
        return;
      }

      var days = Math.floor(distance / (1000 * 60 * 60 * 24));
      var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      var seconds = Math.floor((distance % (1000 * 60)) / 1000);

      document.getElementById("demo").textContent = days + "d " + hours + "h " + minutes + "m " + seconds + "s ";
    }, 1000);
  })();