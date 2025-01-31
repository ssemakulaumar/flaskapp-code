public interface ApiService {
    @GET("/api/visualize")
    Call<JsonObject> getVisualization();
}
