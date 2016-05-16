var mainModule = angular.module('ananke-main',['angularSpinners']);
            
mainModule.controller('nodeController',function($scope,$http,spinnerService) {
                
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
        //$scope.status = 'waiting';
        //spinnerService.show('wait');
        $http.get('api/startcluster',{params: {}}).success(function(data, status, headers, config) {
            $scope.status = 'master';
        }).error(function(data, status, headers, config) {});
    };
    
    $scope.join_cluster = function() {
        //$scope.status = 'waiting';
        //spinnerService.show('wait');
        var masterip = ([$scope.ipchunks[0].i, $scope.ipchunks[1].i, $scope.chunk3, $scope.chunk4]).join('.');
        $http.get('api/joincluster',{params: {'ip':masterip}}).success(function(data, status, headers, config) {
            $scope.status = 'slave';
        }).error(function(data, status, headers, config) {});
    };
    
        
});

mainModule.controller('docController',function($scope,$http) {
    
    $http.get('api/getdocs',{params: {}}).success(function(data, status, headers, config) {
        $scope.allthedocs = data.allthedocs;
    }).error(function(data, status, headers, config) {
    });    

    
});    