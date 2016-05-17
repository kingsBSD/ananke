var mainModule = angular.module('ananke-main',['angularSpinners']);
            
mainModule.controller('nodeController',function($scope,$http,spinnerService) {

    var msg = {'master_active':0}
    
    var auto_conn = new WebSocket("ws://127.0.0.1:5001");
    auto_conn.onopen = function () {
    };
    
    auto_conn.onmessage = function(e) {
        switch (parseInt(msg[e.data])) {
            case 0: $scope.status = 'master'; spinnerService.hide('wait'); break;
        }    
    }    
    
    $scope.chunk3 = {};
    $scope.chunk4 = {};
    $scope.error = {};
    
    $http.get('api/status',{params: {}}).success(function(data, status, headers, config) {
        if (data.network) {
            $scope.ipchunks = [{i:data.ip[0]}, {i:data.ip[1]}];
            $scope.master_url=data.ip.join('.')+":5050";
        }
        $scope.status = data.status;
    }).error(function(data, status, headers, config) {
        $scope.ipchunks = [{i:0}, {i:0}];
    });
                    
    $scope.start_cluster = function() {
        $scope.status = 'waiting';
        spinnerService.show('wait');
        $http.get('api/startcluster',{params: {}}).success(function(data, status, headers, config) {
            if (!data.okay) {
                $scope.error.msg = data.error;
                $scope.status = 'dormant';
                spinnerService.hide('wait');    
            }    
        }).error(function(data, status, headers, config) {});
    };
    
    $scope.join_cluster = function() {
        $scope.status = 'waiting';
        spinnerService.show('wait');
        var masterip = ([$scope.ipchunks[0].i, $scope.ipchunks[1].i, $scope.chunk3.i, $scope.chunk4.i]).join('.');
        $http.get('api/joincluster',{params: {'ip':masterip}}).success(function(data, status, headers, config) {
            if (!data.okay) {
                $scope.error.msg = data.error;
                $scope.status = 'dormant';
                spinnerService.hide('wait');    
            } 
        }).error(function(data, status, headers, config) {});
    };
    
        
});

mainModule.controller('docController',function($scope,$http) {
    
    $http.get('api/getdocs',{params: {}}).success(function(data, status, headers, config) {
        $scope.allthedocs = data.allthedocs;
    }).error(function(data, status, headers, config) {
    });    

    
});    