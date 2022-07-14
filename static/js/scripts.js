let slider = tns({
    container: ".scores-slider",
    "slideBy": "1",
    "controls":false,
    "nav": false,
    "autoplay":true,
    "autoplayButton":false,
    "autoplayButtonOutput": false,
    responsive: {
        1600: {
            items: 8
        },
        1024:{
            items: 8
        },
        768: {
            items: 6
        },
        384:
        {
            items: 3
        }
    }
})