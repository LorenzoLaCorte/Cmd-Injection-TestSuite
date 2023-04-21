<?php

$host = $_GET['host'];

system("ping -c 10 $host");